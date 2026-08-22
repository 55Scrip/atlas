"""Executive Tenure Record + Tenure Context + Guidance History During
Tenure + Tenure Timeline + Track Record Knowledge + Historical
Association Layer (Capability Expansion Sprint 11: Executive Track
Record Intelligence, Phases 2 through 8).

**The deepest composition yet -- a pure aggregation over every prior
Management Intelligence sprint's own already-computed output**:
Executive Change Intelligence (Sprint 10, for tenure identity/windows/
timeline events), Management Guidance Intelligence (Sprint 9, for
guidance history), Management Credibility Intelligence (Sprint 8, for
commitments), plus the already-computed period-level records from
Financial Statement/Capital Allocation/Growth Intelligence (Sprints 3/
4/6). This module computes zero new statistics, zero new
classification, and re-derives nothing any sibling already produced --
it only *filters* each sibling's own already-real, already-dated
records to the tenure window an `ExecutiveIdentity` (Sprint 10) already
carries, via one small, disclosed, reused rule (`classify_association`).

**Phase 9 audit finding**: every record this module links (financial
periods, transcripts, capital-allocation periods, growth observations,
guidance items, commitments) is already covered by an existing
`KnowledgeDomain` (`FINANCIAL_HISTORY`/`EARNINGS_CALL_ANALYSIS`/
`CAPITAL_ALLOCATION`/`GROWTH`). This module introduces no new
`BusinessFactKind`, no new `SourceKind`, and no new provider call -- it
is a pure, further aggregation of already-covered evidence, the
identical precedent Financial Quality/Business Quality/Management
Credibility/Executive Change Intelligence already established. No new
`KnowledgeDomain` is registered.

**The single most load-bearing discipline in this module**: "occurred
during this executive's tenure" is never conflated with "occurred
because of this executive." Every linked record is exactly that -- a
record whose own real date falls inside the tenure's own real,
evidence-observed window (`classify_association`, Phase 8) -- never a
computed verdict about whether the tenure was good, bad, responsible,
or causal. This module deliberately does **not** recompute a tenure-
scoped Business Quality/Financial Quality/Growth Intelligence verdict:
those capabilities are whole-company aggregates with no tenure-windowed
recomputation in this codebase, and building one here would be exactly
the "duplicate calculations" this sprint's own Phase 3 instruction
forbids, as well as a real risk of exactly this sprint's own non-goal
("never attribute company-wide outcomes to a single executive merely
because they served during that period") -- a "business quality during
this CEO's tenure" verdict reads as an evaluation of that CEO even when
not intended as one. Instead, this module exposes the real, dated,
period-level evidence a reader can inspect directly, and nothing more.

**Guidance linkage (Phase 4) is filtered by both date window and
speaker identity** (`GuidanceItem.speaker == executive.name`) -- not
merely "any guidance issued by anyone while this executive served,"
but specifically the guidance *this executive personally issued*,
matching Phase 4's own "guidance history for each executive." Financial
periods/capital-allocation periods/growth observations/commitments,
which carry no speaker attribution, are linked by date window alone --
company-wide evidence observed during the tenure, explicitly not
attributed to the executive's own actions.

**"Completed during tenure" (guidance history) is a real, disclosed
simplification**: it means the guidance item was *issued* during this
tenure and has since reached `GuidanceStatus.COMPLETED` -- the
resolution itself may fall chronologically after the tenure ended,
since `management_guidance_intelligence.py`'s own outcome comparison
only resolves once sufficient subsequent financial periods exist.
Atlas does not claim the resolution was recognized while the executive
was still serving.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.capital_allocation_intelligence import CapitalAllocationHistory, CapitalAllocationPeriod
from atlas.alpha.investment_case.earnings_call import EarningsCallKnowledge, EarningsCallTranscript
from atlas.alpha.investment_case.executive_change_intelligence import (
    ExecutiveChangeKnowledge,
    ExecutiveIdentity,
    LeadershipChangeEvent,
    LeadershipChangeEventType,
)
from atlas.alpha.investment_case.financial_statement_intelligence import FinancialStatementHistory, IncomeStatementPeriod
from atlas.alpha.investment_case.growth_intelligence import GrowthKnowledge, GrowthObservation
from atlas.alpha.investment_case.management_credibility_intelligence import ManagementCommitment, ManagementCredibilityKnowledge
from atlas.alpha.investment_case.management_guidance_intelligence import (
    GuidanceItem,
    GuidanceOutcome,
    GuidanceStatus,
    ManagementGuidanceKnowledge,
    RevisionKind,
)

__all__ = [
    "TemporalAssociation",
    "classify_association",
    "EvidenceCompleteness",
    "TenureContext",
    "TenureGuidanceHistory",
    "TenureTimeline",
    "TrackRecordFindingKind",
    "TrackRecordFinding",
    "ExecutiveTenureRecord",
    "ExecutiveTrackRecordKnowledge",
    "extract_executive_track_record",
]


# -- Phase 8: Historical Association Layer -----------------------------------


class TemporalAssociation(str, Enum):
    BEFORE_TENURE = "before_tenure"
    DURING_TENURE = "during_tenure"
    AFTER_TENURE = "after_tenure"


def classify_association(item_date: date, tenure_start: date, tenure_end: date) -> TemporalAssociation:
    """The one rule every filter in this module uses -- kept public so
    a future capability can apply the identical, disclosed association
    logic itself rather than reimplementing it."""
    if item_date < tenure_start:
        return TemporalAssociation.BEFORE_TENURE
    if item_date > tenure_end:
        return TemporalAssociation.AFTER_TENURE
    return TemporalAssociation.DURING_TENURE


def _during(item_date: date, tenure_start: date, tenure_end: date) -> bool:
    return classify_association(item_date, tenure_start, tenure_end) is TemporalAssociation.DURING_TENURE


# -- Phase 2: Executive Tenure Record ----------------------------------------


class EvidenceCompleteness(str, Enum):
    """How many distinct transcripts back this tenure's own observed
    window -- reuses `ExecutiveIdentity.source_transcripts` directly,
    a disclosed count, never a fabricated precision claim about actual
    tenure length."""

    SINGLE_OBSERVATION = "single_observation"
    PARTIAL_HISTORY = "partial_history"
    SUBSTANTIAL_HISTORY = "substantial_history"


_PARTIAL_HISTORY_MIN_TRANSCRIPTS = 2
_SUBSTANTIAL_HISTORY_MIN_TRANSCRIPTS = 4
"""Reuses the identical disclosed threshold Executive Change
Intelligence's own `_MIN_TRANSCRIPTS_FOR_LONG_TENURE` (Sprint 10)
already establishes -- the same cadence assumption, not a new number."""


def _evidence_completeness(executive: ExecutiveIdentity) -> EvidenceCompleteness:
    count = len(executive.source_transcripts)
    if count >= _SUBSTANTIAL_HISTORY_MIN_TRANSCRIPTS:
        return EvidenceCompleteness.SUBSTANTIAL_HISTORY
    if count >= _PARTIAL_HISTORY_MIN_TRANSCRIPTS:
        return EvidenceCompleteness.PARTIAL_HISTORY
    return EvidenceCompleteness.SINGLE_OBSERVATION


# -- Phase 3 + 5: Tenure Context (observable evidence, never a verdict) ------


@dataclass(frozen=True)
class TenureContext:
    """Every field is a pure date-window filter over an already-real,
    already-computed sibling record -- never a new aggregate, never a
    verdict. See this module's own docstring for why no Business/
    Financial Quality "during tenure" verdict is computed here."""

    financial_periods: tuple[IncomeStatementPeriod, ...]
    earnings_calls: tuple[EarningsCallTranscript, ...]
    capital_allocation_periods: tuple[CapitalAllocationPeriod, ...]
    growth_observations: tuple[GrowthObservation, ...]
    """Sprint 6's own revenue observations, filtered to the tenure
    window -- the single most representative already-computed growth
    series, reused rather than choosing among six possible metrics."""
    commitments: tuple[ManagementCommitment, ...]
    """Sprint 8's own commitments, filtered by date window only (not
    speaker) -- company-wide commitment evidence observed during the
    tenure, not necessarily this executive's own statements."""


def _tenure_context(
    executive: ExecutiveIdentity, financial_statement_history: FinancialStatementHistory,
    earnings_call: EarningsCallKnowledge, capital_allocation_history: CapitalAllocationHistory,
    growth: GrowthKnowledge, commitments: tuple[ManagementCommitment, ...],
) -> TenureContext:
    start, end = executive.first_observed_date, executive.last_observed_date
    return TenureContext(
        financial_periods=tuple(
            p for p in financial_statement_history.income_statements if _during(p.period_end, start, end)
        ),
        earnings_calls=tuple(
            t for t in earnings_call.transcripts if _during(t.fiscal_date_ending or t.published_at, start, end)
        ),
        capital_allocation_periods=tuple(
            p for p in capital_allocation_history.periods if _during(p.period_end, start, end)
        ),
        growth_observations=tuple(
            o for o in growth.revenue.observations if _during(o.period_end, start, end)
        ),
        commitments=tuple(c for c in commitments if _during(c.statement_date, start, end)),
    )


# -- Phase 4: Guidance History During Tenure ---------------------------------


@dataclass(frozen=True)
class TenureGuidanceHistory:
    issued: tuple[GuidanceItem, ...]
    """Guidance this specific executive personally issued during their
    own observed tenure window -- filtered by speaker identity, not
    merely date (see this module's own docstring)."""
    revised: tuple[GuidanceItem, ...]
    completed: tuple[GuidanceItem, ...]
    unresolved: tuple[GuidanceItem, ...]
    fulfilled: tuple[GuidanceItem, ...]
    withdrawn: tuple[GuidanceItem, ...]


_REVISION_KINDS = (RevisionKind.RAISED, RevisionKind.LOWERED, RevisionKind.REAFFIRMED, RevisionKind.UNCHANGED)


def _guidance_history(executive: ExecutiveIdentity, guidance_items: tuple[GuidanceItem, ...]) -> TenureGuidanceHistory:
    start, end = executive.first_observed_date, executive.last_observed_date
    issued = tuple(
        g for g in guidance_items if g.speaker == executive.name and _during(g.statement_date, start, end)
    )
    return TenureGuidanceHistory(
        issued=issued,
        revised=tuple(g for g in issued if g.revision_kind in _REVISION_KINDS),
        completed=tuple(g for g in issued if g.status is GuidanceStatus.COMPLETED),
        unresolved=tuple(g for g in issued if g.outcome is GuidanceOutcome.UNRESOLVED),
        fulfilled=tuple(g for g in issued if g.outcome is GuidanceOutcome.FULFILLED),
        withdrawn=tuple(g for g in issued if g.status is GuidanceStatus.WITHDRAWN),
    )


# -- Phase 6: Tenure Timeline -------------------------------------------------


@dataclass(frozen=True)
class TenureTimeline:
    own_events: tuple[LeadershipChangeEvent, ...]
    """This executive's own appointment/departure/role-change events
    (Sprint 10), filtered by name and role category -- never
    recomputed, only selected."""
    overlapping_executives: tuple[ExecutiveIdentity, ...]
    """Every other executive whose own observed window intersects this
    one's -- a real, evidence-based overlap, never an inferred
    reporting relationship."""


def _tenure_timeline(
    executive: ExecutiveIdentity, all_executives: tuple[ExecutiveIdentity, ...],
    all_events: tuple[LeadershipChangeEvent, ...],
) -> TenureTimeline:
    own_events = tuple(
        e for e in all_events if e.executive_name == executive.name and e.role_category is executive.role_category
    )
    overlapping = tuple(
        other for other in all_executives
        if other.name != executive.name
        and other.first_observed_date <= executive.last_observed_date
        and other.last_observed_date >= executive.first_observed_date
    )
    return TenureTimeline(own_events=own_events, overlapping_executives=overlapping)


# -- Phase 7 + 11: Track Record Knowledge + Explainability -------------------


class TrackRecordFindingKind(str, Enum):
    """Closed, presence-only findings -- never a score, never a
    ranking, never a judgment about the executive (this sprint's own
    "provide context, not judgment" guiding principle)."""

    GUIDANCE_ACTIVITY_OBSERVED = "guidance_activity_observed"
    COMMUNICATION_ACTIVITY_OBSERVED = "communication_activity_observed"
    CAPITAL_ALLOCATION_ACTIVITY_OBSERVED = "capital_allocation_activity_observed"
    COMMITMENTS_LINKED = "commitments_linked"
    LEADERSHIP_TRANSITION_DURING_TENURE = "leadership_transition_during_tenure"
    INSUFFICIENT_TENURE_EVIDENCE = "insufficient_tenure_evidence"


@dataclass(frozen=True)
class TrackRecordFinding:
    kind: TrackRecordFindingKind
    evidence_count: int
    """A disclosed count of the supporting records -- the full records
    themselves are already available on this tenure's own `context`/
    `guidance_history`/`timeline` fields, never duplicated here."""


def _findings(context: TenureContext, guidance_history: TenureGuidanceHistory, timeline: TenureTimeline) -> tuple[TrackRecordFinding, ...]:
    findings: list[TrackRecordFinding] = []

    if guidance_history.issued:
        findings.append(TrackRecordFinding(kind=TrackRecordFindingKind.GUIDANCE_ACTIVITY_OBSERVED, evidence_count=len(guidance_history.issued)))
    if context.earnings_calls:
        findings.append(TrackRecordFinding(kind=TrackRecordFindingKind.COMMUNICATION_ACTIVITY_OBSERVED, evidence_count=len(context.earnings_calls)))
    if context.capital_allocation_periods:
        findings.append(
            TrackRecordFinding(
                kind=TrackRecordFindingKind.CAPITAL_ALLOCATION_ACTIVITY_OBSERVED, evidence_count=len(context.capital_allocation_periods),
            )
        )
    if context.commitments:
        findings.append(TrackRecordFinding(kind=TrackRecordFindingKind.COMMITMENTS_LINKED, evidence_count=len(context.commitments)))

    role_changes = tuple(e for e in timeline.own_events if e.event_type is LeadershipChangeEventType.ROLE_CHANGE)
    if timeline.overlapping_executives or role_changes:
        findings.append(
            TrackRecordFinding(
                kind=TrackRecordFindingKind.LEADERSHIP_TRANSITION_DURING_TENURE,
                evidence_count=len(timeline.overlapping_executives) + len(role_changes),
            )
        )

    if not findings:
        findings.append(TrackRecordFinding(kind=TrackRecordFindingKind.INSUFFICIENT_TENURE_EVIDENCE, evidence_count=0))

    return tuple(findings)


# -- Composition ---------------------------------------------------------------


@dataclass(frozen=True)
class ExecutiveTenureRecord:
    executive: ExecutiveIdentity
    evidence_completeness: EvidenceCompleteness
    context: TenureContext
    guidance_history: TenureGuidanceHistory
    timeline: TenureTimeline
    findings: tuple[TrackRecordFinding, ...]


@dataclass(frozen=True)
class ExecutiveTrackRecordKnowledge:
    tenures: tuple[ExecutiveTenureRecord, ...]
    """One record per `ExecutiveIdentity` Sprint 10 already produced --
    same count, same order, never a re-derivation of who held what
    role."""


def extract_executive_track_record(
    executive_change: ExecutiveChangeKnowledge,
    financial_statement_history: FinancialStatementHistory,
    earnings_call: EarningsCallKnowledge,
    capital_allocation_history: CapitalAllocationHistory,
    growth: GrowthKnowledge,
    management_credibility: ManagementCredibilityKnowledge,
    management_guidance: ManagementGuidanceKnowledge,
) -> ExecutiveTrackRecordKnowledge:
    """Pure, no I/O. `executive_change.executives == ()` yields an
    empty track record -- never a fabricated tenure history."""
    tenures: list[ExecutiveTenureRecord] = []
    for executive in executive_change.executives:
        context = _tenure_context(
            executive, financial_statement_history, earnings_call, capital_allocation_history, growth,
            management_credibility.commitments,
        )
        guidance_history = _guidance_history(executive, management_guidance.guidance_items)
        timeline = _tenure_timeline(executive, executive_change.executives, executive_change.leadership_changes)
        tenures.append(
            ExecutiveTenureRecord(
                executive=executive, evidence_completeness=_evidence_completeness(executive), context=context,
                guidance_history=guidance_history, timeline=timeline,
                findings=_findings(context, guidance_history, timeline),
            )
        )
    return ExecutiveTrackRecordKnowledge(tenures=tuple(tenures))
