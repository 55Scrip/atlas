"""The Recommendation Conviction engine itself -- pure, deterministic,
no I/O. Given the exact same `ConvictionInputs`, every function here
always returns the exact same result.

**`ConvictionStrength` is derived from exactly two already-computed
signals, capped against each other -- never a new judgement.** The
base value comes straight from `atlas.analysis_engine.conviction
.ConvictionLevel` (already "how strongly does available analysis
support a conclusion"); it is then capped by `DecisionReadinessStatus`
(Sprint 11) so a Case whose own readiness process is `BLOCKED`/
`UNAVAILABLE`/`WAITING` can never show a conviction stronger than that
process itself has earned -- the identical discipline that fixed
Sprint 11's own READY-with-blockers incoherence (`decision_readiness
.engine`'s own docstring) applies here: two independently-maintained
"how good is this" signals must never be allowed to disagree, so one
is always the ceiling on the other, never a second vote. A Case with
`DecisionAction.NO_DECISION` (Sprint 1) never has a `ConvictionStrength`
above `UNAVAILABLE` at all -- there is no recommendation yet to hold a
conviction about.

**`RecommendationStability` is a second, independent axis**, derived
from the same readiness blockers/thesis-staleness/evidence-graph facts
Sprint 1 and Sprint 10 already computed -- never the same waterfall as
`ConvictionStrength`, since "how strong" and "how robust" are
deliberately different questions (see this package's own `__init__.py`).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.decision_readiness.models import DecisionBlocker, DecisionBlockerKind, DecisionReadinessReason, DecisionReadinessStatus
from atlas.alpha.evidence_graph.models import WeaknessKind
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import (
    ConvictionChange,
    ConvictionComparison,
    ConvictionReason,
    ConvictionReasonSource,
    ConvictionStrength,
    ConvictionSummary,
    PortfolioConvictionBreakdown,
    RecommendationConviction,
    RecommendationStability,
)
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel, ConvictionReasonCode

__all__ = [
    "ConvictionInputs",
    "build_conviction",
    "summarize_conviction",
    "compare_convictions",
    "detect_conviction_change",
    "build_portfolio_conviction_breakdown",
]


@dataclass(frozen=True)
class ConvictionInputs:
    action: DecisionAction
    readiness_status: DecisionReadinessStatus
    readiness_blockers: tuple[DecisionBlocker, ...]
    readiness_supporting_reasons: tuple[DecisionReadinessReason, ...]
    analysis_conviction: ConvictionAssessment
    weak_dependency_kinds: tuple[WeaknessKind, ...]
    """Every distinct `WeaknessKind` present in the Case's own Evidence
    Graph (Sprint 10) -- deduplicated by the caller, in `WeaknessKind`'s
    own declared order, for determinism."""
    is_thesis_stale: bool


_STRENGTH_FROM_ANALYSIS_CONVICTION: dict[ConvictionLevel, ConvictionStrength] = {
    ConvictionLevel.VERY_HIGH: ConvictionStrength.VERY_STRONG,
    ConvictionLevel.HIGH: ConvictionStrength.STRONG,
    ConvictionLevel.MODERATE: ConvictionStrength.MODERATE,
    ConvictionLevel.LOW: ConvictionStrength.WEAK,
    ConvictionLevel.INSUFFICIENT_EVIDENCE: ConvictionStrength.VERY_WEAK,
}
"""A direct, exhaustive re-expression of the existing five-level scale
into this package's own six-level one -- never a threshold invented
here. `UNAVAILABLE` has no entry: it is reached only via the
`DecisionAction.NO_DECISION` gate below, never from an analysis level."""

_STRENGTH_RANK = {
    ConvictionStrength.UNAVAILABLE: -1,
    ConvictionStrength.VERY_WEAK: 0,
    ConvictionStrength.WEAK: 1,
    ConvictionStrength.MODERATE: 2,
    ConvictionStrength.STRONG: 3,
    ConvictionStrength.VERY_STRONG: 4,
}

_READINESS_CAP: dict[DecisionReadinessStatus, ConvictionStrength | None] = {
    DecisionReadinessStatus.READY: None,
    DecisionReadinessStatus.ALMOST_READY: ConvictionStrength.MODERATE,
    DecisionReadinessStatus.WAITING: ConvictionStrength.WEAK,
    DecisionReadinessStatus.BLOCKED: ConvictionStrength.VERY_WEAK,
    DecisionReadinessStatus.UNAVAILABLE: ConvictionStrength.VERY_WEAK,
    DecisionReadinessStatus.UNKNOWN: ConvictionStrength.VERY_WEAK,
}
"""`None` means "no ceiling" -- only `READY` earns that. Every other
status caps the analysis-derived base value at a fixed, declared
maximum, so conviction can never read stronger than Atlas's own
readiness process has actually earned."""

_POSITIVE_ANALYSIS_REASONS = frozenset(
    {
        ConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
        ConvictionReasonCode.NO_CONTRADICTING_EVIDENCE,
        ConvictionReasonCode.THESIS_NOT_STALE,
        ConvictionReasonCode.NO_OPEN_QUESTIONS,
        ConvictionReasonCode.BUSINESS_AND_VALUATION_CONCLUSIVE,
        ConvictionReasonCode.NO_HIGH_FINANCIAL_OR_VALUATION_RISK,
    }
)
_NEGATIVE_ANALYSIS_REASONS = frozenset(
    {
        ConvictionReasonCode.UPSTREAM_STAGE_NOT_EVALUATED,
        ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,
        ConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL,
        ConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT,
        ConvictionReasonCode.THESIS_STALE,
        ConvictionReasonCode.OPEN_QUESTIONS_REMAIN,
        ConvictionReasonCode.BUSINESS_OR_VALUATION_NOT_YET_CONCLUSIVE,
        ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT,
    }
)
"""`ConvictionReasonCode`'s own members already come in fixed positive/
negative pairs (`conviction.py`'s own `base_reasons` construction always
picks one of each pair) -- this is a direct reading of that existing
polarity, not a new classification invented here."""

_OPERATIONAL_BLOCKER_KINDS = frozenset(
    {
        DecisionBlockerKind.NEVER_EVALUATED,
        DecisionBlockerKind.MONITORING_FAILED,
        DecisionBlockerKind.MONITORING_PENDING,
        DecisionBlockerKind.OPERATIONAL_FRESHNESS_OUTDATED,
        DecisionBlockerKind.NO_DATA_SOURCE,
    }
)
_EVIDENCE_LIMITING_BLOCKER_KINDS = frozenset(
    {
        DecisionBlockerKind.MISSING_OBSERVATION,
        DecisionBlockerKind.MISSING_THESIS_EVIDENCE,
        DecisionBlockerKind.COVERAGE_INCOMPLETE,
        DecisionBlockerKind.UNKNOWN_VALUATION,
        DecisionBlockerKind.INSUFFICIENT_EVIDENCE,
    }
)
"""The identical evidence-limiting subset Sprint 1's own `engine.py`
already established (`_EVIDENCE_LIMITING_BLOCKER_KINDS`) -- reused
verbatim, not re-derived."""

_STABILITY_RANK = {
    RecommendationStability.OPERATIONALLY_BLOCKED: 0,
    RecommendationStability.EVIDENCE_LIMITED: 1,
    RecommendationStability.FRAGILE: 2,
    RecommendationStability.WAITING_FOR_EVIDENCE: 3,
    RecommendationStability.STABLE: 4,
}


def _derive_strength(inputs: ConvictionInputs) -> ConvictionStrength:
    if inputs.action is DecisionAction.NO_DECISION:
        return ConvictionStrength.UNAVAILABLE
    base = _STRENGTH_FROM_ANALYSIS_CONVICTION[inputs.analysis_conviction.level]
    cap = _READINESS_CAP[inputs.readiness_status]
    if cap is None or _STRENGTH_RANK[base] <= _STRENGTH_RANK[cap]:
        return base
    return cap


def _derive_stability(inputs: ConvictionInputs) -> RecommendationStability:
    blocker_kinds = {b.kind for b in inputs.readiness_blockers}
    if blocker_kinds & _OPERATIONAL_BLOCKER_KINDS:
        return RecommendationStability.OPERATIONALLY_BLOCKED
    if blocker_kinds & _EVIDENCE_LIMITING_BLOCKER_KINDS:
        return RecommendationStability.EVIDENCE_LIMITED
    if inputs.readiness_status in (DecisionReadinessStatus.WAITING, DecisionReadinessStatus.ALMOST_READY):
        return RecommendationStability.WAITING_FOR_EVIDENCE
    if inputs.is_thesis_stale or inputs.weak_dependency_kinds:
        return RecommendationStability.FRAGILE
    return RecommendationStability.STABLE


def _supporting_reasons(inputs: ConvictionInputs) -> tuple[ConvictionReason, ...]:
    reasons = tuple(
        ConvictionReason(ConvictionReasonSource.READINESS_SUPPORT, reason.kind.value)
        for reason in inputs.readiness_supporting_reasons
    )
    reasons += tuple(
        ConvictionReason(ConvictionReasonSource.ANALYSIS_CONVICTION, code.value)
        for code in inputs.analysis_conviction.reasons
        if code in _POSITIVE_ANALYSIS_REASONS
    )
    return reasons


def _limiting_reasons(inputs: ConvictionInputs) -> tuple[ConvictionReason, ...]:
    reasons = tuple(
        ConvictionReason(ConvictionReasonSource.READINESS_BLOCKER, blocker.kind.value)
        for blocker in inputs.readiness_blockers
    )
    reasons += tuple(
        ConvictionReason(ConvictionReasonSource.ANALYSIS_CONVICTION, code.value)
        for code in inputs.analysis_conviction.reasons
        if code in _NEGATIVE_ANALYSIS_REASONS
    )
    reasons += tuple(
        ConvictionReason(ConvictionReasonSource.EVIDENCE_GRAPH, kind.value) for kind in inputs.weak_dependency_kinds
    )
    return reasons


def build_conviction(case_id: str, inputs: ConvictionInputs, *, generated_at: datetime) -> RecommendationConviction:
    limiting = _limiting_reasons(inputs)
    return RecommendationConviction(
        case_id=case_id,
        action=inputs.action,
        strength=_derive_strength(inputs),
        stability=_derive_stability(inputs),
        supporting_reasons=_supporting_reasons(inputs),
        limiting_reasons=limiting,
        strengthening_trigger=limiting[0] if limiting else None,
        generated_at=generated_at,
    )


def summarize_conviction(conviction: RecommendationConviction) -> ConvictionSummary:
    return ConvictionSummary(
        case_id=conviction.case_id,
        action=conviction.action,
        strength=conviction.strength,
        stability=conviction.stability,
        primary_supporting_reason=conviction.supporting_reasons[0] if conviction.supporting_reasons else None,
        primary_limiting_reason=conviction.limiting_reasons[0] if conviction.limiting_reasons else None,
        strengthening_trigger=conviction.strengthening_trigger,
        generated_at=conviction.generated_at,
    )


def _pick(a_value: int, b_value: int, a_id: str, b_id: str) -> str | None:
    if a_value > b_value:
        return a_id
    if b_value > a_value:
        return b_id
    return None


def compare_convictions(a: RecommendationConviction, b: RecommendationConviction) -> ConvictionComparison:
    """Deliverable 9 -- four independent factual comparisons, each
    `None` on a genuine tie. Never a combined "winner": the four
    fields can point in different directions for the same pair (a
    stronger recommendation can still be the more evidence-limited
    one), and that disagreement is itself real information, never
    collapsed into one verdict."""
    stronger = _pick(_STRENGTH_RANK[a.strength], _STRENGTH_RANK[b.strength], a.case_id, b.case_id)
    more_stable = _pick(_STABILITY_RANK[a.stability], _STABILITY_RANK[b.stability], a.case_id, b.case_id)

    a_evidence_limited = a.stability is RecommendationStability.EVIDENCE_LIMITED
    b_evidence_limited = b.stability is RecommendationStability.EVIDENCE_LIMITED
    more_evidence_limited = _pick(int(a_evidence_limited), int(b_evidence_limited), a.case_id, b.case_id)

    a_operationally_blocked = a.stability is RecommendationStability.OPERATIONALLY_BLOCKED
    b_operationally_blocked = b.stability is RecommendationStability.OPERATIONALLY_BLOCKED
    more_operationally_blocked = _pick(int(a_operationally_blocked), int(b_operationally_blocked), a.case_id, b.case_id)

    return ConvictionComparison(
        a=a,
        b=b,
        stronger_case_id=stronger,
        more_evidence_limited_case_id=more_evidence_limited,
        more_operationally_blocked_case_id=more_operationally_blocked,
        more_stable_case_id=more_stable,
    )


def detect_conviction_change(
    previous: RecommendationConviction | None, current: RecommendationConviction, *, detected_at: datetime
) -> ConvictionChange | None:
    """"No event, no timestamp" -- `None` when this is the first-ever
    computation, or when neither `strength` nor `stability` actually
    moved."""
    if previous is None:
        return None
    if previous.strength == current.strength and previous.stability == current.stability:
        return None

    previous_set = set(previous.limiting_reasons)
    current_set = set(current.limiting_reasons)
    return ConvictionChange(
        case_id=current.case_id,
        previous_strength=previous.strength,
        current_strength=current.strength,
        previous_stability=previous.stability,
        current_stability=current.stability,
        new_limiting_reasons=tuple(r for r in current.limiting_reasons if r in current_set - previous_set),
        resolved_limiting_reasons=tuple(r for r in previous.limiting_reasons if r in previous_set - current_set),
        detected_at=detected_at,
    )


_HIGH_STRENGTHS = frozenset({ConvictionStrength.VERY_STRONG, ConvictionStrength.STRONG})
_LOW_STRENGTHS = frozenset({ConvictionStrength.VERY_WEAK, ConvictionStrength.WEAK})


def build_portfolio_conviction_breakdown(
    items: tuple[tuple[str, RecommendationConviction], ...],
) -> PortfolioConvictionBreakdown:
    """Deliverable 7 -- ticker groupings only, in the caller's own
    existing order (Portfolio's own holdings order); never re-ranked,
    never turned into an allocation suggestion."""
    return PortfolioConvictionBreakdown(
        highest_conviction=tuple(ticker for ticker, c in items if c.strength in _HIGH_STRENGTHS),
        lowest_conviction=tuple(ticker for ticker, c in items if c.strength in _LOW_STRENGTHS),
        evidence_limited=tuple(ticker for ticker, c in items if c.stability is RecommendationStability.EVIDENCE_LIMITED),
        operationally_blocked=tuple(
            ticker for ticker, c in items if c.stability is RecommendationStability.OPERATIONALLY_BLOCKED
        ),
    )
