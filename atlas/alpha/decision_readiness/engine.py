"""The Decision Readiness Engine itself (Deliverable 3), Blocker
Detection (Deliverable 4), and Readiness Explanation (Deliverable 5).
Every function here is pure and deterministic -- no AI, no
probabilities, no percentages, no averaging, no I/O. Input is a small
bundle of already-computed real signals (`ReadinessInputs`); output is
`DecisionReadinessStatus` plus exhaustive blocker/reason lists.

**Why a priority-ordered waterfall, not a score.** Every other closed-
outcome engine in this codebase (`atlas.alpha.monitoring.engine
.derive_operational_status`, `atlas.alpha.ingestion.engine
.derive_data_freshness_status`) already uses the identical pattern: a
fixed sequence of real, named conditions, first match wins. This module
follows it rather than inventing a new "readiness score" -- Deliverable
3's own explicit instruction.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadiness,
    DecisionReadinessChange,
    DecisionReadinessComparison,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
    DecisionReadinessSummary,
)
from atlas.alpha.decision_support import DecisionSupportLevel
from atlas.alpha.coverage.models import ConfidenceLevel
from atlas.alpha.ingestion.engine import DataFreshnessStatus
from atlas.alpha.stance.models import StanceLevel
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.valuation.support import ValuationSupportGapKind, ValuationSupportStatus

__all__ = [
    "ReadinessInputs",
    "derive_decision_readiness",
    "detect_blockers",
    "detect_supporting_reasons",
    "summarize_readiness",
    "compare_readiness",
    "detect_readiness_change",
    "READINESS_PROXIMITY_RANK",
]


@dataclass(frozen=True)
class ReadinessInputs:
    """Every real, already-computed fact this engine reads -- nothing
    here is derived by this module; each field is a direct value from
    an existing engine (see this package's own `__init__.py` for
    exactly which one)."""

    coverage_level: AnalysisCoverageLevel
    confidence_level: ConfidenceLevel | None
    decision_support_level: DecisionSupportLevel
    valuation_support_status: ValuationSupportStatus
    valuation_support_gap: ValuationSupportGapKind | None
    stance_level: StanceLevel | None
    observation_count: int
    has_conflicting_evidence_finding: bool
    no_support_finding_count: int
    has_critical_dependency: bool
    is_monitoring_pending: bool
    last_monitored_at: datetime | None
    last_run_failed_for_case: bool
    data_freshness_status: DataFreshnessStatus


_OPERATIONALLY_UNAVAILABLE_FRESHNESS = (DataFreshnessStatus.MONITORING_FAILED, DataFreshnessStatus.NO_DATA_SOURCE, DataFreshnessStatus.UNKNOWN)
_OUTDATED_FRESHNESS = (DataFreshnessStatus.WAITING_FOR_ANALYSIS,)
"""Only `WAITING_FOR_ANALYSIS` (new/replaced data detected, not yet
recomputed) is an "operational freshness outdated" blocker.
`WAITING_FOR_NEW_DATA` is deliberately excluded -- per its own
docstring (`atlas.alpha.ingestion.engine.DataFreshnessStatus`), it
means "Ingestion checked and found nothing new," Sprint 9's own
steady, healthy state, not a blocker. Treating it as one would flag
every genuinely current Case as outdated."""


_CONCLUSIVE_BUT_MIXED_VALUATION_GAPS = frozenset(
    {ValuationSupportGapKind.SCENARIO_ENVELOPE_INCONCLUSIVE, ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS}
)
"""Atlas Intelligence Sprint 12 (Analysis Coverage Expansion, Deliverable
5) -- audited against a real company (AAPL): `ValuationSupportStatus
.INSUFFICIENT_INPUT` does not always mean "Atlas doesn't know the
valuation." `SCENARIO_ENVELOPE_INCONCLUSIVE` means Atlas built a real,
historically-grounded forward-return range and that range genuinely
straddles zero; `CONFLICTING_VALUATION_PROOFS` means two independent,
real proofs disagree. Both are a *complete*, honest analysis whose
answer is "genuinely mixed," not an unanswered question -- the
`unknown_valuation` blocker name would overstate the gap. The other
`ValuationSupportGapKind` members (`MISSING_CAPITAL_DEPLOYMENT
_VALUATION_SUPPORT`/`NO_DURABLE_GROWTH_BASIS`/
`INSUFFICIENT_HISTORICAL_VALUATION_DATA`/`NO_SUFFICIENT_VALUATION_PROOF`)
are real data shortfalls and keep blocking readiness unchanged."""

_UNAVAILABLE_BLOCKER_KINDS = frozenset(
    {DecisionBlockerKind.NEVER_EVALUATED, DecisionBlockerKind.MONITORING_FAILED, DecisionBlockerKind.NO_DATA_SOURCE}
)
_BLOCKED_BLOCKER_KINDS = frozenset(
    {
        DecisionBlockerKind.CONFLICTING_EVIDENCE,
        DecisionBlockerKind.AVOID_DECISION_SIGNAL,
        DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED,
    }
)
"""Every other real `DecisionBlockerKind` (`MONITORING_PENDING`/
`OPERATIONAL_FRESHNESS_OUTDATED`/`COVERAGE_INCOMPLETE`/
`INSUFFICIENT_EVIDENCE`/`UNKNOWN_VALUATION`/`MISSING_OBSERVATION`/
`MISSING_THESIS_EVIDENCE`) means `WAITING` -- nothing is actively
wrong, there simply isn't enough yet."""


def derive_decision_readiness(inputs: ReadinessInputs) -> DecisionReadinessStatus:
    """Deliverable 3 -- one status, derived from the exact same
    blocker set `detect_blockers` returns (never a second, independent
    condition list -- Live Verification, Deliverable 15, found that
    keeping these as two separately-maintained lists let a Case be
    reported `READY` while `detect_blockers` still listed real
    blockers, an incoherent, untrustworthy result; see this function's
    own history in the Final Report). `NO_COVERAGE` is the one
    genuine floor check that precedes blocker detection entirely --
    every blocker below presupposes at least some real company data
    exists to reason about."""
    if inputs.coverage_level is AnalysisCoverageLevel.NO_COVERAGE:
        return DecisionReadinessStatus.UNKNOWN

    blocker_kinds = {blocker.kind for blocker in detect_blockers(inputs)}
    if blocker_kinds & _UNAVAILABLE_BLOCKER_KINDS:
        return DecisionReadinessStatus.UNAVAILABLE
    if blocker_kinds & _BLOCKED_BLOCKER_KINDS:
        return DecisionReadinessStatus.BLOCKED
    if blocker_kinds:
        return DecisionReadinessStatus.WAITING

    if inputs.confidence_level in (ConfidenceLevel.LIMITED, ConfidenceLevel.VERY_LIMITED, None):
        return DecisionReadinessStatus.ALMOST_READY

    return DecisionReadinessStatus.READY


def detect_blockers(inputs: ReadinessInputs) -> tuple[DecisionBlocker, ...]:
    """Deliverable 4 -- exhaustive, not just the one that decided
    `status` (mirrors `ConvictionReasonCode`'s "every applicable code"
    discipline). Fixed, declared order -- never re-sorted by severity."""
    blockers: list[DecisionBlocker] = []

    if inputs.last_monitored_at is None:
        blockers.append(DecisionBlocker(DecisionBlockerKind.NEVER_EVALUATED))
    if inputs.last_run_failed_for_case:
        blockers.append(DecisionBlocker(DecisionBlockerKind.MONITORING_FAILED))
    if inputs.data_freshness_status is DataFreshnessStatus.NO_DATA_SOURCE:
        blockers.append(DecisionBlocker(DecisionBlockerKind.NO_DATA_SOURCE))
    if inputs.has_conflicting_evidence_finding:
        blockers.append(DecisionBlocker(DecisionBlockerKind.CONFLICTING_EVIDENCE))
    if inputs.stance_level is StanceLevel.AVOID_DECISION:
        blockers.append(DecisionBlocker(DecisionBlockerKind.AVOID_DECISION_SIGNAL))
    if inputs.has_critical_dependency:
        blockers.append(DecisionBlocker(DecisionBlockerKind.CRITICAL_DEPENDENCY_UNRESOLVED))
    if inputs.is_monitoring_pending:
        blockers.append(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING))
    if inputs.data_freshness_status in _OUTDATED_FRESHNESS:
        blockers.append(DecisionBlocker(DecisionBlockerKind.OPERATIONAL_FRESHNESS_OUTDATED))
    if inputs.coverage_level is AnalysisCoverageLevel.PARTIAL_COVERAGE:
        blockers.append(DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE))
    if inputs.decision_support_level is DecisionSupportLevel.INSUFFICIENT_EVIDENCE:
        blockers.append(DecisionBlocker(DecisionBlockerKind.INSUFFICIENT_EVIDENCE))
    if (
        inputs.valuation_support_status is ValuationSupportStatus.INSUFFICIENT_INPUT
        and inputs.valuation_support_gap not in _CONCLUSIVE_BUT_MIXED_VALUATION_GAPS
    ):
        blockers.append(DecisionBlocker(DecisionBlockerKind.UNKNOWN_VALUATION))
    if inputs.observation_count == 0:
        blockers.append(DecisionBlocker(DecisionBlockerKind.MISSING_OBSERVATION))
    if inputs.no_support_finding_count > 0:
        blockers.append(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE, detail=inputs.no_support_finding_count))

    return tuple(blockers)


def detect_supporting_reasons(inputs: ReadinessInputs) -> tuple[DecisionReadinessReason, ...]:
    """Deliverable 5's own structured half -- the positive facts a
    "ready because..." explanation is built from. Fixed, declared
    order, same discipline as `detect_blockers`."""
    reasons: list[DecisionReadinessReason] = []

    if inputs.coverage_level is AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE:
        reasons.append(DecisionReadinessReason(DecisionReadinessReasonKind.SUBSTANTIAL_COVERAGE_REACHED))
    if inputs.confidence_level is ConfidenceLevel.HIGH:
        reasons.append(DecisionReadinessReason(DecisionReadinessReasonKind.CONFIDENCE_ESTABLISHED))
    if not inputs.has_conflicting_evidence_finding:
        reasons.append(DecisionReadinessReason(DecisionReadinessReasonKind.NO_CONFLICTS_FOUND))
    if not inputs.is_monitoring_pending and inputs.last_monitored_at is not None:
        reasons.append(DecisionReadinessReason(DecisionReadinessReasonKind.MONITORING_CURRENT))
    if inputs.decision_support_level is not DecisionSupportLevel.INSUFFICIENT_EVIDENCE:
        reasons.append(DecisionReadinessReason(DecisionReadinessReasonKind.DECISION_SUPPORT_REACHED))
    if not inputs.has_critical_dependency:
        reasons.append(DecisionReadinessReason(DecisionReadinessReasonKind.NO_CRITICAL_DEPENDENCIES))

    return tuple(reasons)


def summarize_readiness(readiness: DecisionReadiness) -> DecisionReadinessSummary:
    """Deliverable 6/7 -- `primary_*` is simply the first entry of each
    already-fixed-order tuple; no separately invented "most important"
    ranking."""
    return DecisionReadinessSummary(
        case_id=readiness.case_id,
        status=readiness.status,
        primary_blocker=readiness.blockers[0] if readiness.blockers else None,
        primary_supporting_reason=readiness.supporting_reasons[0] if readiness.supporting_reasons else None,
        generated_at=readiness.generated_at,
    )


READINESS_PROXIMITY_RANK: dict[DecisionReadinessStatus, int] = {
    DecisionReadinessStatus.READY: 0,
    DecisionReadinessStatus.ALMOST_READY: 1,
    DecisionReadinessStatus.WAITING: 2,
    DecisionReadinessStatus.BLOCKED: 3,
    DecisionReadinessStatus.UNAVAILABLE: 4,
    DecisionReadinessStatus.UNKNOWN: 5,
}
"""Deliverable 9's own "closer to decision readiness" ordering -- a
fixed, declared rank (lower is closer), never a computed distance.
`BLOCKED` ranks closer than `UNAVAILABLE`: a blocked Case has real
analysis and a real, nameable problem; an unavailable one has no
trustworthy read from Atlas's own systems at all -- one step further
back. `UNKNOWN` is the floor: no real company data exists yet."""


def compare_readiness(a: DecisionReadiness, b: DecisionReadiness) -> DecisionReadinessComparison:
    """Deliverable 9 -- "ingen rekommendation": `closer_case_id` is
    `None` whenever both sides tie in proximity rank, an honest tie
    rather than an arbitrary tiebreak."""
    rank_a = READINESS_PROXIMITY_RANK[a.status]
    rank_b = READINESS_PROXIMITY_RANK[b.status]
    if rank_a < rank_b:
        closer = a.case_id
    elif rank_b < rank_a:
        closer = b.case_id
    else:
        closer = None

    kinds_a = {blocker.kind for blocker in a.blockers}
    kinds_b = {blocker.kind for blocker in b.blockers}
    differing = tuple(sorted((kinds_a ^ kinds_b), key=lambda k: k.value))

    return DecisionReadinessComparison(a=a, b=b, closer_case_id=closer, differing_blocker_kinds=differing)


def detect_readiness_change(
    previous: DecisionReadiness | None, current: DecisionReadiness, *, detected_at: datetime
) -> DecisionReadinessChange | None:
    """Deliverable 10/11 -- `None` whenever nothing real changed
    (`previous is None`, the first-ever computation, or an identical
    status *and* an identical blocker set): never a manufactured
    "change" from a Case simply being read twice, the same "no event,
    no timestamp" discipline `atlas.alpha.evidence_timeline`/
    `atlas.analysis_engine.investment_case_change` already establish
    for their own snapshot comparisons.

    **Live Verification finding (Deliverable 15), fixed here.** Status
    alone under-reports real change: a Case can stay `UNAVAILABLE`
    (e.g. `no_data_source` persists) while a *different* real blocker
    (`monitoring_pending`) genuinely resolves underneath it -- exactly
    Deliverable 10's own "Operational blocker resolved" example, which
    names no status transition at all. A change is now reported
    whenever status *or* the blocker set differs."""
    if previous is None:
        return None
    previous_kinds = {b.kind for b in previous.blockers}
    current_kinds = {b.kind for b in current.blockers}
    if previous.status == current.status and previous_kinds == current_kinds:
        return None
    return DecisionReadinessChange(
        case_id=current.case_id,
        previous_status=previous.status,
        current_status=current.status,
        new_blockers=tuple(sorted(current_kinds - previous_kinds, key=lambda k: k.value)),
        resolved_blockers=tuple(sorted(previous_kinds - current_kinds, key=lambda k: k.value)),
        detected_at=detected_at,
    )
