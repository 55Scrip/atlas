"""Management Commitment Knowledge + Commitment Tracking + Outcome
Comparison + Communication Consistency + Guidance Reliability +
Management Credibility Knowledge (Capability Expansion Sprint 8:
Management Credibility Intelligence, Phases 2 through 7).

**A pure, higher-order aggregation over Earnings Call Intelligence
(Sprint 2)'s own already-classified statements, cross-referenced
against Financial Statement Intelligence (Sprint 3)/Growth Intelligence
(Sprint 6)/Capital Allocation Intelligence (Sprint 4)'s own already-
computed period-level figures.** This module introduces zero new
natural-language classification: `earnings_call.py`'s own `_classify`
keyword machinery (Sprint 2) already tags every `ManagementStatement`
with a closed set of `CommentaryCategory` members, including
`MANAGEMENT_COMMITMENTS`, `MANAGEMENT_GUIDANCE`, and `GUIDANCE_CHANGES`
-- exactly the forward-looking, commitment-signaling language this
sprint's own Phase 2 asks for. This module reuses that existing
classification directly rather than inventing a second NLP pass, per
this sprint's own "must not redesign Earnings Call Intelligence
extraction" non-goal.

**Phase 1 audit finding**: none of Financial Statement/Growth/Business
Quality Intelligence carry any notion of a management statement or a
forward commitment -- they are purely numeric. Earnings Call
Intelligence is the only existing capability that already extracts
management language, and it already does the one piece of
classification work this sprint needs (Sprint 2's own `CommentaryCategory`
taxonomy already names every category Phase 2's own bullet list asks
for: "profitability"/"margin" commitments -> `MARGIN_COMMENTARY`,
"cost reduction" commitments -> `COST_COMMENTARY`, "growth" commitments
-> `GROWTH_DRIVERS`, "capital allocation"/"investment" commitments ->
`CAPITAL_ALLOCATION_COMMENTARY`). No new `CommentaryCategory` member is
added.

**Outcome Comparison (Phase 4) is a deliberately coarse, disclosed,
category-level comparison -- never a claim that a specific commitment
quote was semantically verified against a specific number.** Atlas has
no semantic-parsing capability to extract a quantified target (e.g.
"expand gross margin by 200bps") from free text, and inventing one
would be exactly the "fabricate management intent" this sprint's own
non-goals forbid. Instead, a commitment classified into one of four
metric-linking categories (growth/margin/cost-reduction/capital-
allocation, via the statement's own pre-existing Sprint-2 category
membership -- e.g. a statement matching both `MANAGEMENT_GUIDANCE` and
`MARGIN_COMMENTARY` is treated as a trackable margin-related guidance
statement) is compared against that category's already-computed
period-level figures for every period strictly after the commitment's
own reporting period, using the identical later-half/earlier-half
trend-direction algorithm every sibling capability already duplicates.
A commitment with no metric-linking category (`GENERAL` -- pure
"we are committed to X" framing with no identifiable financial topic)
always resolves to `INSUFFICIENT_EVIDENCE`, honestly, rather than
guessing which metric it might have meant.

**Guidance revision direction (`raised`/`lowered`) reuses the literal
keyword substrings already present in Sprint 2's own `GUIDANCE_CHANGES`
keyword tuple** (`"raised guidance"`/`"raising our outlook"` vs.
`"lowered guidance"`/`"reducing our outlook"`) -- a further, disclosed
subdivision of an already-classified bucket via the identical exact-
substring mechanism Sprint 2 already trusts, not a new classifier.
`"revised guidance"`/`"updated guidance"` are genuinely ambiguous
(direction not stated) and resolve to `UNSPECIFIED`, honestly.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.capital_allocation_intelligence import CapitalAllocationHistory
from atlas.alpha.investment_case.earnings_call import (
    CommentaryCategory,
    EarningsCallChangeIntelligence,
    EarningsCallKnowledge,
    EmphasisChange,
    SentimentTrend,
    compute_change_intelligence,
)
from atlas.alpha.investment_case.financial_statement_intelligence import FinancialStatementHistory, TrendDirection
from atlas.alpha.investment_case.growth_intelligence import GrowthKnowledge

__all__ = [
    "TrendDirection",
    "CommitmentSignal",
    "CommitmentCategory",
    "CommitmentOutcome",
    "GuidanceRevisionDirection",
    "ManagementCommitment",
    "CommunicationDirection",
    "CommunicationConsistency",
    "GuidanceReliabilityKnowledge",
    "ExecutionConsistency",
    "CredibilityFindingKind",
    "CredibilityFinding",
    "ManagementCredibilityKnowledge",
    "extract_management_commitments",
    "extract_management_credibility",
]

_MIN_PERIODS_FOR_OUTCOME_TREND = 3
_TREND_THRESHOLD = 0.1


def _windowed_direction(values: tuple[float, ...]) -> TrendDirection:
    """The identical later-half/earlier-half trend algorithm every
    sibling capability already duplicates, applied here to a *windowed*
    subset (periods strictly after one commitment's own reporting
    period) of already-computed sibling values -- never a new metric,
    never a re-read of raw `BusinessRecord`s."""
    if len(values) < _MIN_PERIODS_FOR_OUTCOME_TREND:
        return TrendDirection.INSUFFICIENT_DATA
    spread = max(values) - min(values)
    if spread == 0:
        return TrendDirection.STABLE
    midpoint = len(values) // 2
    earlier_avg = sum(values[:midpoint]) / midpoint
    later_avg = sum(values[midpoint:]) / (len(values) - midpoint)
    relative_change = (later_avg - earlier_avg) / spread
    if relative_change > _TREND_THRESHOLD:
        return TrendDirection.RISING
    if relative_change < -_TREND_THRESHOLD:
        return TrendDirection.FALLING
    return TrendDirection.STABLE


# -- Phase 2 + 3: Management Commitment Knowledge + Commitment Tracking ----


class CommitmentSignal(str, Enum):
    """Which of Sprint 2's own forward-looking `CommentaryCategory`
    members triggered extraction -- priority order when a statement
    matches more than one: a guidance revision is the most specific and
    informative signal, then guidance, then a general commitment."""

    GUIDANCE_REVISION = "guidance_revision"
    GUIDANCE = "guidance"
    COMMITMENT = "commitment"


class CommitmentCategory(str, Enum):
    """The financial topic this commitment can honestly be linked to,
    via the statement's own Sprint-2 category membership -- `GENERAL`
    when no metric-linking category is present (Phase 2's own "do not
    infer commitments": Atlas does not guess a topic that was not
    itself keyword-classified)."""

    GROWTH = "growth"
    MARGIN = "margin"
    COST_REDUCTION = "cost_reduction"
    CAPITAL_ALLOCATION = "capital_allocation"
    GENERAL = "general"


class CommitmentOutcome(str, Enum):
    """Phase 4's own closed vocabulary. See this module's own docstring
    for exactly what "fulfilled" means here: a coarse, disclosed,
    category-level directional comparison, never per-statement semantic
    verification."""

    FULFILLED = "fulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    UNRESOLVED = "unresolved"
    NO_OBSERVABLE_OUTCOME_YET = "no_observable_outcome_yet"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class GuidanceRevisionDirection(str, Enum):
    RAISED = "raised"
    LOWERED = "lowered"
    UNSPECIFIED = "unspecified"


@dataclass(frozen=True)
class ManagementCommitment:
    """Every field Phase 3 asks for -- statement date, reporting
    period, speaker, source transcript, commitment category, supporting
    quotation -- plus the Phase 4 outcome. `supporting_quotation` is
    always the verbatim `ManagementStatement.content` Sprint 2 already
    carries -- never rewritten."""

    signal: CommitmentSignal
    commitment_category: CommitmentCategory
    statement_date: date
    reporting_period: str
    """The transcript's own `quarter` (e.g. `"2026Q2"`) -- Alpha
    Vantage's own format, unchanged."""
    fiscal_date_ending: date | None
    speaker: str
    source_transcript: str
    """The same `reporting_period` string, named separately per Phase
    3's own field list -- this codebase has no other transcript
    identifier than its own `quarter` label."""
    supporting_quotation: str
    revision_direction: GuidanceRevisionDirection | None
    """Only set when `signal is GUIDANCE_REVISION`; `None` for every
    other signal -- honestly absent, not a default."""
    outcome: CommitmentOutcome


_SIGNAL_PRIORITY: tuple[tuple[CommentaryCategory, CommitmentSignal], ...] = (
    (CommentaryCategory.GUIDANCE_CHANGES, CommitmentSignal.GUIDANCE_REVISION),
    (CommentaryCategory.MANAGEMENT_GUIDANCE, CommitmentSignal.GUIDANCE),
    (CommentaryCategory.MANAGEMENT_COMMITMENTS, CommitmentSignal.COMMITMENT),
)
_METRIC_CATEGORY_PRIORITY: tuple[tuple[CommentaryCategory, CommitmentCategory], ...] = (
    (CommentaryCategory.GROWTH_DRIVERS, CommitmentCategory.GROWTH),
    (CommentaryCategory.MARGIN_COMMENTARY, CommitmentCategory.MARGIN),
    (CommentaryCategory.COST_COMMENTARY, CommitmentCategory.COST_REDUCTION),
    (CommentaryCategory.CAPITAL_ALLOCATION_COMMENTARY, CommitmentCategory.CAPITAL_ALLOCATION),
)
_RAISED_KEYWORDS = ("raised guidance", "raising our outlook")
_LOWERED_KEYWORDS = ("lowered guidance", "reducing our outlook")
"""Duplicated (not imported) from the identical literal substrings
already present in `earnings_call._CATEGORY_KEYWORDS[GUIDANCE_CHANGES]`
-- that mapping is private, and this is the same "small justified
duplication over touching a protected sibling" every prior sprint's own
module already establishes."""


def _signal_for(categories: tuple[CommentaryCategory, ...]) -> CommitmentSignal | None:
    for source_category, signal in _SIGNAL_PRIORITY:
        if source_category in categories:
            return signal
    return None


def _commitment_category_for(categories: tuple[CommentaryCategory, ...]) -> CommitmentCategory:
    for source_category, commitment_category in _METRIC_CATEGORY_PRIORITY:
        if source_category in categories:
            return commitment_category
    return CommitmentCategory.GENERAL


def _revision_direction(content: str) -> GuidanceRevisionDirection:
    lowered = content.lower()
    if any(keyword in lowered for keyword in _RAISED_KEYWORDS):
        return GuidanceRevisionDirection.RAISED
    if any(keyword in lowered for keyword in _LOWERED_KEYWORDS):
        return GuidanceRevisionDirection.LOWERED
    return GuidanceRevisionDirection.UNSPECIFIED


# -- Phase 4: Outcome Comparison -------------------------------------------


def _subsequent_margin_values(history: FinancialStatementHistory, attribute: str, after: date) -> tuple[float, ...]:
    return tuple(
        getattr(period, attribute) for period in history.income_statements
        if period.period_end > after and getattr(period, attribute) is not None
    )


def _subsequent_revenue_values(growth: GrowthKnowledge, after: date) -> tuple[float, ...]:
    return tuple(
        observation.value for observation in growth.revenue.observations
        if observation.period_end > after and observation.value is not None
    )


def _subsequent_capital_values(history: CapitalAllocationHistory, attribute: str, after: date) -> tuple[float, ...]:
    return tuple(
        getattr(period, attribute) for period in history.periods
        if period.period_end > after and getattr(period, attribute) is not None
    )


def _outcome_from_directions(directions: tuple[TrendDirection, ...], favorable: TrendDirection) -> CommitmentOutcome:
    known = tuple(direction for direction in directions if direction is not TrendDirection.INSUFFICIENT_DATA)
    if not known:
        return CommitmentOutcome.INSUFFICIENT_EVIDENCE
    favorable_count = sum(1 for direction in known if direction is favorable)
    if favorable_count == len(known):
        return CommitmentOutcome.FULFILLED
    if favorable_count == 0:
        return CommitmentOutcome.UNRESOLVED
    return CommitmentOutcome.PARTIALLY_FULFILLED


def _commitment_outcome(
    category: CommitmentCategory, after: date, financial_statement_history: FinancialStatementHistory,
    growth: GrowthKnowledge, capital_allocation_history: CapitalAllocationHistory,
) -> CommitmentOutcome:
    if category is CommitmentCategory.GENERAL:
        return CommitmentOutcome.INSUFFICIENT_EVIDENCE

    if category is CommitmentCategory.GROWTH:
        if not any(o.period_end > after for o in growth.revenue.observations):
            return CommitmentOutcome.NO_OBSERVABLE_OUTCOME_YET
        direction = _windowed_direction(_subsequent_revenue_values(growth, after))
        return _outcome_from_directions((direction,), TrendDirection.RISING)

    if category is CommitmentCategory.MARGIN:
        if not any(p.period_end > after for p in financial_statement_history.income_statements):
            return CommitmentOutcome.NO_OBSERVABLE_OUTCOME_YET
        direction = _windowed_direction(_subsequent_margin_values(financial_statement_history, "net_margin", after))
        return _outcome_from_directions((direction,), TrendDirection.RISING)

    if category is CommitmentCategory.COST_REDUCTION:
        if not any(p.period_end > after for p in financial_statement_history.income_statements):
            return CommitmentOutcome.NO_OBSERVABLE_OUTCOME_YET
        direction = _windowed_direction(
            _subsequent_margin_values(financial_statement_history, "operating_margin", after)
        )
        return _outcome_from_directions((direction,), TrendDirection.RISING)

    if category is CommitmentCategory.CAPITAL_ALLOCATION:
        if not any(p.period_end > after for p in capital_allocation_history.periods):
            return CommitmentOutcome.NO_OBSERVABLE_OUTCOME_YET
        buybacks = _windowed_direction(_subsequent_capital_values(capital_allocation_history, "share_buybacks", after))
        dividends = _windowed_direction(_subsequent_capital_values(capital_allocation_history, "dividends", after))
        return _outcome_from_directions((buybacks, dividends), TrendDirection.RISING)

    return CommitmentOutcome.INSUFFICIENT_EVIDENCE


def extract_management_commitments(
    earnings_call: EarningsCallKnowledge, financial_statement_history: FinancialStatementHistory,
    growth: GrowthKnowledge, capital_allocation_history: CapitalAllocationHistory,
) -> tuple[ManagementCommitment, ...]:
    """Pure, no I/O. Every commitment traces back to one real, already-
    classified `ManagementStatement` -- never inferred, never
    generated. Empty when no transcript matches a commitment-signaling
    category."""
    commitments: list[ManagementCommitment] = []
    for transcript in earnings_call.transcripts:
        anchor = transcript.fiscal_date_ending or transcript.published_at
        for statement in transcript.statements:
            signal = _signal_for(statement.categories)
            if signal is None:
                continue
            category = _commitment_category_for(statement.categories)
            outcome = _commitment_outcome(
                category, anchor, financial_statement_history, growth, capital_allocation_history
            )
            commitments.append(
                ManagementCommitment(
                    signal=signal, commitment_category=category, statement_date=transcript.published_at,
                    reporting_period=transcript.quarter, fiscal_date_ending=transcript.fiscal_date_ending,
                    speaker=statement.speaker, source_transcript=transcript.quarter,
                    supporting_quotation=statement.content,
                    revision_direction=(
                        _revision_direction(statement.content) if signal is CommitmentSignal.GUIDANCE_REVISION else None
                    ),
                    outcome=outcome,
                )
            )
    return tuple(commitments)


# -- Phase 5: Communication Consistency ------------------------------------


class CommunicationDirection(str, Enum):
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    STABLE = "stable"
    MIXED = "mixed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class CommunicationConsistency:
    """Phase 5. A pure re-labeling of Sprint 2's own already-computed
    `EarningsCallChangeIntelligence` -- zero new sentiment/emphasis
    computation."""

    direction: CommunicationDirection
    strengthened_categories: tuple[CommentaryCategory, ...]
    weakened_categories: tuple[CommentaryCategory, ...]
    guidance_changed: bool
    """`True` only when management made at least one statement this
    quarter Sprint 2 itself classified as `GUIDANCE_CHANGES` -- a real,
    grounded fact, never inferred motive."""
    strategic_emphasis_shifted: bool
    """`True` only when `STRATEGIC_PRIORITIES`'s own already-computed
    `emphasis_change` is a real change, not `STABLE_EMPHASIS`/
    `INSUFFICIENT_DATA`."""


def _communication_consistency(change: EarningsCallChangeIntelligence) -> CommunicationConsistency:
    if change.previous_quarter is None:
        return CommunicationConsistency(
            direction=CommunicationDirection.INSUFFICIENT_DATA, strengthened_categories=(), weakened_categories=(),
            guidance_changed=False, strategic_emphasis_shifted=False,
        )

    strengthened: list[CommentaryCategory] = []
    weakened: list[CommentaryCategory] = []
    guidance_changed = False
    strategic_emphasis_shifted = False
    for category_change in change.category_changes:
        if category_change.sentiment_trend is SentimentTrend.RISING:
            strengthened.append(category_change.category)
        elif category_change.sentiment_trend is SentimentTrend.FALLING:
            weakened.append(category_change.category)
        elif category_change.sentiment_trend is SentimentTrend.INSUFFICIENT_DATA:
            if category_change.emphasis_change in (EmphasisChange.INCREASED_EMPHASIS, EmphasisChange.NEWLY_PRESENT):
                strengthened.append(category_change.category)
            elif category_change.emphasis_change in (EmphasisChange.DECREASED_EMPHASIS, EmphasisChange.NO_LONGER_PRESENT):
                weakened.append(category_change.category)

        if category_change.category is CommentaryCategory.GUIDANCE_CHANGES and category_change.current_statement_count > 0:
            guidance_changed = True
        if category_change.category is CommentaryCategory.STRATEGIC_PRIORITIES and category_change.emphasis_change not in (
            EmphasisChange.STABLE_EMPHASIS, EmphasisChange.INSUFFICIENT_DATA,
        ):
            strategic_emphasis_shifted = True

    if strengthened and weakened:
        direction = CommunicationDirection.MIXED
    elif strengthened:
        direction = CommunicationDirection.STRENGTHENED
    elif weakened:
        direction = CommunicationDirection.WEAKENED
    else:
        direction = CommunicationDirection.STABLE

    return CommunicationConsistency(
        direction=direction, strengthened_categories=tuple(strengthened), weakened_categories=tuple(weakened),
        guidance_changed=guidance_changed, strategic_emphasis_shifted=strategic_emphasis_shifted,
    )


# -- Phase 6: Guidance Reliability -----------------------------------------


@dataclass(frozen=True)
class GuidanceReliabilityKnowledge:
    """Phase 6. A pure grouping/count over the already-built commitment
    list above -- zero new computation."""

    guidance_history: tuple[ManagementCommitment, ...]
    """Every commitment whose `signal` is `GUIDANCE` or `GUIDANCE_
    REVISION` -- guidance statements and guidance revisions both, in
    original chronological order."""
    guidance_revisions: tuple[ManagementCommitment, ...]
    """The `GUIDANCE_REVISION`-signal subset of `guidance_history`."""
    fulfilled_guidance_count: int
    withdrawn_guidance_count: int
    """Guidance revisions whose own `revision_direction is LOWERED`."""
    unresolved_guidance_count: int


def _guidance_reliability(commitments: tuple[ManagementCommitment, ...]) -> GuidanceReliabilityKnowledge:
    guidance_history = tuple(
        c for c in commitments if c.signal in (CommitmentSignal.GUIDANCE, CommitmentSignal.GUIDANCE_REVISION)
    )
    guidance_revisions = tuple(c for c in commitments if c.signal is CommitmentSignal.GUIDANCE_REVISION)
    return GuidanceReliabilityKnowledge(
        guidance_history=guidance_history,
        guidance_revisions=guidance_revisions,
        fulfilled_guidance_count=sum(1 for c in guidance_history if c.outcome is CommitmentOutcome.FULFILLED),
        withdrawn_guidance_count=sum(
            1 for c in guidance_revisions if c.revision_direction is GuidanceRevisionDirection.LOWERED
        ),
        unresolved_guidance_count=sum(
            1 for c in guidance_history
            if c.outcome in (CommitmentOutcome.UNRESOLVED, CommitmentOutcome.PARTIALLY_FULFILLED)
        ),
    )


# -- Phase 7 + 10: Management Credibility Knowledge + Explainability -------


class ExecutionConsistency(str, Enum):
    """Phase 7's own "execution consistency" -- a count over already-
    computed commitment outcomes, restricted to commitments with a real
    resolution (`NO_OBSERVABLE_OUTCOME_YET`/`INSUFFICIENT_EVIDENCE`
    commitments carry no follow-through signal either way and are
    excluded, never treated as failures)."""

    STRONG_FOLLOW_THROUGH = "strong_follow_through"
    MIXED_FOLLOW_THROUGH = "mixed_follow_through"
    WEAK_FOLLOW_THROUGH = "weak_follow_through"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


_RESOLVED_OUTCOMES = (CommitmentOutcome.FULFILLED, CommitmentOutcome.PARTIALLY_FULFILLED, CommitmentOutcome.UNRESOLVED)


def _execution_consistency(commitments: tuple[ManagementCommitment, ...]) -> ExecutionConsistency:
    resolved = tuple(c for c in commitments if c.outcome in _RESOLVED_OUTCOMES)
    if not resolved:
        return ExecutionConsistency.INSUFFICIENT_EVIDENCE
    fulfilled_count = sum(1 for c in resolved if c.outcome is CommitmentOutcome.FULFILLED)
    if fulfilled_count == len(resolved):
        return ExecutionConsistency.STRONG_FOLLOW_THROUGH
    if fulfilled_count == 0:
        return ExecutionConsistency.WEAK_FOLLOW_THROUGH
    return ExecutionConsistency.MIXED_FOLLOW_THROUGH


class CredibilityFindingKind(str, Enum):
    """Closed, presence-only findings -- never combined into a score or
    ranking (this sprint's own "no credibility score" non-goal)."""

    CONSISTENT_FOLLOW_THROUGH = "consistent_follow_through"
    """Evidence supporting credibility (Phase 7): every resolved
    commitment was fulfilled."""
    INCONSISTENT_FOLLOW_THROUGH = "inconsistent_follow_through"
    """Evidence contradicting credibility (Phase 7): no resolved
    commitment was fulfilled."""
    MIXED_FOLLOW_THROUGH = "mixed_follow_through"
    COMMUNICATION_REMAINED_CONSISTENT = "communication_remained_consistent"
    COMMUNICATION_SHIFTED = "communication_shifted"
    GUIDANCE_REVISED_DOWNWARD = "guidance_revised_downward"
    INSUFFICIENT_HISTORY = "insufficient_history"


@dataclass(frozen=True)
class CredibilityFinding:
    kind: CredibilityFindingKind
    supporting_commitments: tuple[ManagementCommitment, ...]
    """The exact `ManagementCommitment` records (speaker, transcript,
    verbatim quotation, outcome) this finding was drawn from -- Phase
    10's own "supporting management statements"/"transcript references"
    requirement, satisfied by embedding the real records directly
    rather than a separate id-based lookup. Empty for the two
    communication-based findings below: their own evidence is already
    fully embedded on `ManagementCredibilityKnowledge.communication_
    consistency`, so nothing is duplicated here."""


def _findings(
    commitments: tuple[ManagementCommitment, ...], execution: ExecutionConsistency,
    communication: CommunicationConsistency, guidance: GuidanceReliabilityKnowledge,
) -> tuple[CredibilityFinding, ...]:
    findings: list[CredibilityFinding] = []

    if execution is ExecutionConsistency.STRONG_FOLLOW_THROUGH:
        findings.append(
            CredibilityFinding(
                kind=CredibilityFindingKind.CONSISTENT_FOLLOW_THROUGH,
                supporting_commitments=tuple(c for c in commitments if c.outcome is CommitmentOutcome.FULFILLED),
            )
        )
    elif execution is ExecutionConsistency.WEAK_FOLLOW_THROUGH:
        findings.append(
            CredibilityFinding(
                kind=CredibilityFindingKind.INCONSISTENT_FOLLOW_THROUGH,
                supporting_commitments=tuple(c for c in commitments if c.outcome is CommitmentOutcome.UNRESOLVED),
            )
        )
    elif execution is ExecutionConsistency.MIXED_FOLLOW_THROUGH:
        findings.append(
            CredibilityFinding(
                kind=CredibilityFindingKind.MIXED_FOLLOW_THROUGH,
                supporting_commitments=tuple(c for c in commitments if c.outcome in _RESOLVED_OUTCOMES),
            )
        )

    if communication.direction is CommunicationDirection.STABLE:
        findings.append(CredibilityFinding(kind=CredibilityFindingKind.COMMUNICATION_REMAINED_CONSISTENT, supporting_commitments=()))
    elif communication.direction in (CommunicationDirection.STRENGTHENED, CommunicationDirection.WEAKENED, CommunicationDirection.MIXED):
        findings.append(CredibilityFinding(kind=CredibilityFindingKind.COMMUNICATION_SHIFTED, supporting_commitments=()))

    if guidance.withdrawn_guidance_count > 0:
        findings.append(
            CredibilityFinding(
                kind=CredibilityFindingKind.GUIDANCE_REVISED_DOWNWARD,
                supporting_commitments=tuple(
                    c for c in guidance.guidance_revisions if c.revision_direction is GuidanceRevisionDirection.LOWERED
                ),
            )
        )

    if not findings:
        findings.append(CredibilityFinding(kind=CredibilityFindingKind.INSUFFICIENT_HISTORY, supporting_commitments=()))

    return tuple(findings)


@dataclass(frozen=True)
class ManagementCredibilityKnowledge:
    commitments: tuple[ManagementCommitment, ...]
    communication_consistency: CommunicationConsistency
    guidance_reliability: GuidanceReliabilityKnowledge
    execution_consistency: ExecutionConsistency
    findings: tuple[CredibilityFinding, ...]


def extract_management_credibility(
    earnings_call: EarningsCallKnowledge,
    financial_statement_history: FinancialStatementHistory,
    growth: GrowthKnowledge,
    capital_allocation_history: CapitalAllocationHistory,
) -> ManagementCredibilityKnowledge:
    """Pure, no I/O. `earnings_call.transcripts == ()` yields every
    dimension at its own honest "insufficient" default -- never a
    fabricated credibility read."""
    commitments = extract_management_commitments(
        earnings_call, financial_statement_history, growth, capital_allocation_history
    )
    communication_consistency = _communication_consistency(compute_change_intelligence(earnings_call))
    guidance_reliability = _guidance_reliability(commitments)
    execution_consistency = _execution_consistency(commitments)
    findings = _findings(commitments, execution_consistency, communication_consistency, guidance_reliability)

    return ManagementCredibilityKnowledge(
        commitments=commitments, communication_consistency=communication_consistency,
        guidance_reliability=guidance_reliability, execution_consistency=execution_consistency, findings=findings,
    )
