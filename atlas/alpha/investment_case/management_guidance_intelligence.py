"""Management Guidance Knowledge Model + Guidance Timeline + Guidance
Classification + Outcome Linking + Revision Intelligence + Guidance
Reliability Knowledge (Capability Expansion Sprint 9: Management
Guidance Intelligence, Phases 2 through 7).

**Phase 1 audit finding**: Earnings Call Intelligence (Sprint 2)
already tags every `ManagementStatement` with `MANAGEMENT_GUIDANCE` and
`GUIDANCE_CHANGES` -- the exact two forward-looking categories this
sprint needs -- via its own keyword classifier. Management Credibility
Intelligence (Sprint 8) already reuses those same two categories for
its own, broader `ManagementCommitment` tracking (alongside `MANAGEMENT_
COMMITMENTS`, which this module deliberately does not read -- Sprint 9
is scoped to guidance specifically, a narrower, more precisely-typed
subset of what Sprint 8 tracks). This module reuses that existing
classification directly; it adds no new `CommentaryCategory` and no new
NLP pass, per this sprint's own "must not redesign Earnings Call
Intelligence extraction" non-goal. It is a sibling of, not a
replacement for, Sprint 8's `ManagementCommitment` -- the two modules
independently extract from the same underlying statements for different
purposes (broad credibility vs. precisely-typed, numeric-target-aware
guidance), the same "small justified duplication over touching a
protected sibling" every prior sprint already establishes.

**Numeric target/range extraction (Phase 2) is deliberately narrow and
purely regex-anchored on literal digit patterns already present in the
verbatim text -- never an estimate.** A percentage (`"8%"`), a percent
range (`"8% to 10%"`), a dollar amount (`"$3 billion"`), or a per-share
figure (`"$1.50 per share"`) is only captured when that exact pattern is
present; every other case leaves both fields `None`, honoring this
sprint's own "if a field is absent from the source transcript, leave it
absent" instruction to the letter.

**Outcome Comparison (Phase 5) is direction-aware, not a fixed "more is
better" assumption**: the favorable outcome direction is derived from
what management's own statement actually said (`GuidanceDirection`) --
guidance to *decrease* capital expenditure is fulfilled by a falling
trend, not a rising one. `RANGE`/`UNKNOWN` direction guidance has no
derivable favorable direction from text alone and always resolves to
`INSUFFICIENT_EVIDENCE` -- Atlas does not guess which side of a stated
range, or an undetected direction, counts as success. This mirrors
Sprint 8's own "never claim per-statement semantic verification, only a
disclosed, category-level directional comparison" discipline, applied
here per-guidance rather than per-commitment-category.

**Guidance Timeline (Phase 3) groups by `GuidanceType` only, ordered
chronologically -- a disclosed, category-level sequencing, not a claim
that two same-type guidance statements target the identical fiscal
period.** Atlas has no semantic capability to parse a natural-language
period reference (e.g. "for the back half of the year" vs. "for fiscal
2026") from free text, and asserting that link would be exactly the
"infer numeric targets/intent that are not explicitly stated" this
sprint's own non-goals forbid. The same limitation, disclosed the same
way, already exists in Sprint 8's own category-level (not per-target)
comparison.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum

from atlas.alpha.investment_case.capital_allocation_intelligence import CapitalAllocationHistory
from atlas.alpha.investment_case.earnings_call import CommentaryCategory, EarningsCallKnowledge
from atlas.alpha.investment_case.financial_statement_intelligence import FinancialStatementHistory, TrendDirection
from atlas.alpha.investment_case.growth_intelligence import GrowthKnowledge, GrowthObservation, GrowthTrendKnowledge

__all__ = [
    "TrendDirection",
    "GuidanceType",
    "GuidanceDirection",
    "TargetUnit",
    "ExplicitTarget",
    "ExplicitTargetRange",
    "ConfidenceWording",
    "GuidanceStatus",
    "GuidanceOutcome",
    "RevisionKind",
    "GuidanceItem",
    "GuidanceReliabilitySummary",
    "ManagementGuidanceKnowledge",
    "extract_management_guidance",
]

_MIN_PERIODS_FOR_OUTCOME_TREND = 3
_TREND_THRESHOLD = 0.1


def _windowed_direction(values: tuple[float, ...]) -> TrendDirection:
    """The identical later-half/earlier-half trend algorithm every
    sibling capability already duplicates, applied to a windowed subset
    (periods strictly after one guidance item's own reporting period)
    of already-computed sibling values."""
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


# -- Phase 4: Guidance Classification ---------------------------------------


class GuidanceType(str, Enum):
    REVENUE = "revenue"
    MARGIN = "margin"
    EPS = "eps"
    FREE_CASH_FLOW = "free_cash_flow"
    CAPITAL_EXPENDITURE = "capital_expenditure"
    GROWTH = "growth"
    PROFITABILITY = "profitability"
    OTHER = "other"


class GuidanceDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"
    RANGE = "range"
    UNKNOWN = "unknown"


class TargetUnit(str, Enum):
    PERCENT = "percent"
    USD_BILLION = "usd_billion"
    USD_MILLION = "usd_million"
    USD_PER_SHARE = "usd_per_share"


@dataclass(frozen=True)
class ExplicitTarget:
    value: float
    unit: TargetUnit


@dataclass(frozen=True)
class ExplicitTargetRange:
    low: float
    high: float
    unit: TargetUnit


class ConfidenceWording(str, Enum):
    CONFIDENT = "confident"
    EXPECTED = "expected"
    TENTATIVE = "tentative"
    UNCERTAIN = "uncertain"
    UNSPECIFIED = "unspecified"


class GuidanceStatus(str, Enum):
    ACTIVE = "active"
    REVISED = "revised"
    WITHDRAWN = "withdrawn"
    COMPLETED = "completed"
    EXPIRED = "expired"
    UNRESOLVED = "unresolved"


class GuidanceOutcome(str, Enum):
    FULFILLED = "fulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    MISSED = "missed"
    UNRESOLVED = "unresolved"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RevisionKind(str, Enum):
    INITIAL = "initial"
    RAISED = "raised"
    LOWERED = "lowered"
    REAFFIRMED = "reaffirmed"
    WITHDRAWN = "withdrawn"
    UNCHANGED = "unchanged"


_EPS_KEYWORDS = ("eps", "earnings per share")
_FCF_KEYWORDS = ("free cash flow", " fcf")
_CAPEX_KEYWORDS = ("capital expenditure", "capex")
_REVENUE_KEYWORDS = ("revenue", "sales")
_WITHDRAWAL_KEYWORDS = (
    "withdrawing our guidance", "withdrawing guidance", "suspending guidance", "no longer providing guidance",
    "pulling our guidance",
)
_INCREASE_KEYWORDS = ("increase", "higher", "grow", "growth", "expand", "improve", "raise", "accelerat")
_DECREASE_KEYWORDS = ("decrease", "lower", "declin", "reduce", "contract", "slow")
_STABLE_KEYWORDS = ("in line with", "consistent with", "maintain", "flat", "unchanged")
_CONFIDENT_KEYWORDS = ("we are confident", "we remain confident")
_UNCERTAIN_KEYWORDS = ("remains uncertain", "difficult to predict", "unable to predict", "not able to forecast")
_TENTATIVE_KEYWORDS = ("we believe", "our current view", "we currently expect")
_EXPECTED_KEYWORDS = ("we expect", "we anticipate", "we forecast", "we project")

_RANGE_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%?\s*(?:to|-|–)\s*(\d+(?:\.\d+)?)\s*%")
_SINGLE_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_USD_BILLION_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)\s*billion", re.IGNORECASE)
_USD_MILLION_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)\s*million", re.IGNORECASE)
_USD_PER_SHARE_RE = re.compile(r"\$\s*(\d+\.\d{2})\b")


def _extract_target_range(content: str) -> ExplicitTargetRange | None:
    match = _RANGE_PERCENT_RE.search(content)
    if match:
        return ExplicitTargetRange(low=float(match.group(1)), high=float(match.group(2)), unit=TargetUnit.PERCENT)
    return None


def _extract_target(content: str, target_range: ExplicitTargetRange | None) -> ExplicitTarget | None:
    """Never populated alongside a range -- a range is reported once,
    as a range, not duplicated as a single point value too."""
    if target_range is not None:
        return None
    lowered = content.lower()
    match = _SINGLE_PERCENT_RE.search(content)
    if match:
        return ExplicitTarget(value=float(match.group(1)), unit=TargetUnit.PERCENT)
    match = _USD_BILLION_RE.search(content)
    if match:
        return ExplicitTarget(value=float(match.group(1)), unit=TargetUnit.USD_BILLION)
    match = _USD_MILLION_RE.search(content)
    if match:
        return ExplicitTarget(value=float(match.group(1)), unit=TargetUnit.USD_MILLION)
    if any(keyword in lowered for keyword in _EPS_KEYWORDS) or "per share" in lowered:
        match = _USD_PER_SHARE_RE.search(content)
        if match:
            return ExplicitTarget(value=float(match.group(1)), unit=TargetUnit.USD_PER_SHARE)
    return None


def _guidance_type(content: str, categories: tuple[CommentaryCategory, ...], explicit_target: ExplicitTarget | None) -> GuidanceType:
    lowered = content.lower()
    if explicit_target is not None and explicit_target.unit is TargetUnit.USD_PER_SHARE:
        return GuidanceType.EPS
    if any(keyword in lowered for keyword in _EPS_KEYWORDS):
        return GuidanceType.EPS
    if any(keyword in lowered for keyword in _FCF_KEYWORDS):
        return GuidanceType.FREE_CASH_FLOW
    if any(keyword in lowered for keyword in _CAPEX_KEYWORDS):
        return GuidanceType.CAPITAL_EXPENDITURE
    if CommentaryCategory.MARGIN_COMMENTARY in categories:
        return GuidanceType.MARGIN
    if any(keyword in lowered for keyword in _REVENUE_KEYWORDS):
        return GuidanceType.REVENUE
    if CommentaryCategory.GROWTH_DRIVERS in categories:
        return GuidanceType.GROWTH
    if CommentaryCategory.COST_COMMENTARY in categories:
        return GuidanceType.PROFITABILITY
    return GuidanceType.OTHER


def _direction(content: str, target_range: ExplicitTargetRange | None) -> GuidanceDirection:
    if target_range is not None:
        return GuidanceDirection.RANGE
    lowered = content.lower()
    increase = any(keyword in lowered for keyword in _INCREASE_KEYWORDS)
    decrease = any(keyword in lowered for keyword in _DECREASE_KEYWORDS)
    stable = any(keyword in lowered for keyword in _STABLE_KEYWORDS)
    if increase and not decrease:
        return GuidanceDirection.INCREASE
    if decrease and not increase:
        return GuidanceDirection.DECREASE
    if stable:
        return GuidanceDirection.STABLE
    return GuidanceDirection.UNKNOWN


def _confidence_wording(content: str) -> ConfidenceWording:
    lowered = content.lower()
    if any(keyword in lowered for keyword in _UNCERTAIN_KEYWORDS):
        return ConfidenceWording.UNCERTAIN
    if any(keyword in lowered for keyword in _CONFIDENT_KEYWORDS):
        return ConfidenceWording.CONFIDENT
    if any(keyword in lowered for keyword in _TENTATIVE_KEYWORDS):
        return ConfidenceWording.TENTATIVE
    if any(keyword in lowered for keyword in _EXPECTED_KEYWORDS):
        return ConfidenceWording.EXPECTED
    return ConfidenceWording.UNSPECIFIED


def _is_withdrawal(content: str) -> bool:
    lowered = content.lower()
    return any(keyword in lowered for keyword in _WITHDRAWAL_KEYWORDS)


# -- Phase 5: Guidance Outcome Linking ---------------------------------------


def _favorable_direction(direction: GuidanceDirection) -> TrendDirection | None:
    if direction is GuidanceDirection.INCREASE:
        return TrendDirection.RISING
    if direction is GuidanceDirection.DECREASE:
        return TrendDirection.FALLING
    if direction is GuidanceDirection.STABLE:
        return TrendDirection.STABLE
    return None


def _subsequent_observation_values(observations: tuple[GrowthObservation, ...], after: date) -> tuple[float, ...]:
    return tuple(o.value for o in observations if o.period_end > after and o.value is not None)


def _any_subsequent_observation(observations: tuple[GrowthObservation, ...], after: date) -> bool:
    return any(o.period_end > after for o in observations)


def _subsequent_period_values(periods, attribute: str, after: date) -> tuple[float, ...]:
    return tuple(getattr(p, attribute) for p in periods if p.period_end > after and getattr(p, attribute) is not None)


def _any_subsequent_period(periods, after: date) -> bool:
    return any(p.period_end > after for p in periods)


def _guidance_outcome(
    guidance_type: GuidanceType, direction: GuidanceDirection, after: date,
    financial_statement_history: FinancialStatementHistory, growth: GrowthKnowledge,
) -> GuidanceOutcome:
    favorable = _favorable_direction(direction)
    if favorable is None:
        return GuidanceOutcome.INSUFFICIENT_EVIDENCE

    growth_trend: GrowthTrendKnowledge | None = None
    if guidance_type in (GuidanceType.REVENUE, GuidanceType.GROWTH):
        growth_trend = growth.revenue
    elif guidance_type is GuidanceType.EPS:
        growth_trend = growth.earnings_per_share
    elif guidance_type is GuidanceType.PROFITABILITY:
        growth_trend = growth.earnings
    elif guidance_type is GuidanceType.FREE_CASH_FLOW:
        growth_trend = growth.free_cash_flow

    if growth_trend is not None:
        if not _any_subsequent_observation(growth_trend.observations, after):
            return GuidanceOutcome.UNRESOLVED
        trend = _windowed_direction(_subsequent_observation_values(growth_trend.observations, after))
    elif guidance_type is GuidanceType.MARGIN:
        if not _any_subsequent_period(financial_statement_history.income_statements, after):
            return GuidanceOutcome.UNRESOLVED
        trend = _windowed_direction(
            _subsequent_period_values(financial_statement_history.income_statements, "net_margin", after)
        )
    elif guidance_type is GuidanceType.CAPITAL_EXPENDITURE:
        if not _any_subsequent_period(financial_statement_history.cash_flow_statements, after):
            return GuidanceOutcome.UNRESOLVED
        trend = _windowed_direction(
            _subsequent_period_values(financial_statement_history.cash_flow_statements, "capital_expenditure", after)
        )
    else:
        return GuidanceOutcome.INSUFFICIENT_EVIDENCE

    if trend is TrendDirection.INSUFFICIENT_DATA:
        return GuidanceOutcome.INSUFFICIENT_EVIDENCE
    if trend is favorable:
        return GuidanceOutcome.FULFILLED
    if trend is TrendDirection.STABLE:
        return GuidanceOutcome.PARTIALLY_FULFILLED
    return GuidanceOutcome.MISSED


# -- Phase 2, 3, 6, 10: Guidance Item ----------------------------------------


@dataclass(frozen=True)
class GuidanceItem:
    """Every field Phase 2 asks for, plus Phase 4's status, Phase 5's
    outcome, and Phase 6's revision kind. `supporting_quotation` is
    always the verbatim `ManagementStatement.content` Sprint 2 already
    carries -- Phase 2's own "management statement" and "supporting
    quotation" bullets name the identical verbatim text, represented
    once here rather than duplicated under two field names."""

    guidance_type: GuidanceType
    speaker: str
    reporting_period: str
    statement_date: date
    fiscal_date_ending: date | None
    source_transcript: str
    direction: GuidanceDirection
    explicit_target: ExplicitTarget | None
    explicit_target_range: ExplicitTargetRange | None
    confidence_wording: ConfidenceWording
    supporting_quotation: str
    status: GuidanceStatus
    revision_kind: RevisionKind
    outcome: GuidanceOutcome


@dataclass(frozen=True)
class _RawGuidance:
    guidance_type: GuidanceType
    speaker: str
    reporting_period: str
    statement_date: date
    fiscal_date_ending: date | None
    source_transcript: str
    direction: GuidanceDirection
    explicit_target: ExplicitTarget | None
    explicit_target_range: ExplicitTargetRange | None
    confidence_wording: ConfidenceWording
    supporting_quotation: str
    is_withdrawal: bool
    anchor: date


def _extract_raw_guidance(earnings_call: EarningsCallKnowledge) -> tuple[_RawGuidance, ...]:
    raw: list[_RawGuidance] = []
    for transcript in earnings_call.transcripts:
        anchor = transcript.fiscal_date_ending or transcript.published_at
        for statement in transcript.statements:
            if not (
                CommentaryCategory.MANAGEMENT_GUIDANCE in statement.categories
                or CommentaryCategory.GUIDANCE_CHANGES in statement.categories
            ):
                continue
            target_range = _extract_target_range(statement.content)
            target = _extract_target(statement.content, target_range)
            raw.append(
                _RawGuidance(
                    guidance_type=_guidance_type(statement.content, statement.categories, target),
                    speaker=statement.speaker, reporting_period=transcript.quarter,
                    statement_date=transcript.published_at, fiscal_date_ending=transcript.fiscal_date_ending,
                    source_transcript=transcript.quarter, direction=_direction(statement.content, target_range),
                    explicit_target=target, explicit_target_range=target_range,
                    confidence_wording=_confidence_wording(statement.content),
                    supporting_quotation=statement.content, is_withdrawal=_is_withdrawal(statement.content),
                    anchor=anchor,
                )
            )
    return tuple(raw)


def _revision_kind(current: _RawGuidance, previous: _RawGuidance | None) -> RevisionKind:
    if current.is_withdrawal:
        return RevisionKind.WITHDRAWN
    if previous is None:
        return RevisionKind.INITIAL
    if current.explicit_target is not None and previous.explicit_target is not None and current.explicit_target.unit is previous.explicit_target.unit:
        if current.explicit_target.value > previous.explicit_target.value:
            return RevisionKind.RAISED
        if current.explicit_target.value < previous.explicit_target.value:
            return RevisionKind.LOWERED
        return RevisionKind.REAFFIRMED
    if (
        current.explicit_target_range is not None and previous.explicit_target_range is not None
        and current.explicit_target_range.unit is previous.explicit_target_range.unit
    ):
        current_mid = (current.explicit_target_range.low + current.explicit_target_range.high) / 2
        previous_mid = (previous.explicit_target_range.low + previous.explicit_target_range.high) / 2
        if current_mid > previous_mid:
            return RevisionKind.RAISED
        if current_mid < previous_mid:
            return RevisionKind.LOWERED
        return RevisionKind.REAFFIRMED
    if current.direction is GuidanceDirection.INCREASE and previous.direction is not GuidanceDirection.INCREASE:
        return RevisionKind.RAISED
    if current.direction is GuidanceDirection.DECREASE and previous.direction is not GuidanceDirection.DECREASE:
        return RevisionKind.LOWERED
    if current.direction is previous.direction:
        return RevisionKind.REAFFIRMED
    return RevisionKind.UNCHANGED


def _status(
    current: _RawGuidance, is_latest_in_group: bool, outcome: GuidanceOutcome, period_completed: bool,
) -> GuidanceStatus:
    if current.is_withdrawal:
        return GuidanceStatus.WITHDRAWN
    if not is_latest_in_group:
        return GuidanceStatus.REVISED
    if outcome in (GuidanceOutcome.FULFILLED, GuidanceOutcome.PARTIALLY_FULFILLED, GuidanceOutcome.MISSED):
        return GuidanceStatus.COMPLETED
    if period_completed:
        return GuidanceStatus.EXPIRED
    return GuidanceStatus.ACTIVE


def _period_completed(guidance_type: GuidanceType, after: date, financial_statement_history: FinancialStatementHistory, growth: GrowthKnowledge) -> bool:
    if guidance_type in (GuidanceType.REVENUE, GuidanceType.GROWTH):
        return _any_subsequent_observation(growth.revenue.observations, after)
    if guidance_type is GuidanceType.EPS:
        return _any_subsequent_observation(growth.earnings_per_share.observations, after)
    if guidance_type is GuidanceType.PROFITABILITY:
        return _any_subsequent_observation(growth.earnings.observations, after)
    if guidance_type is GuidanceType.FREE_CASH_FLOW:
        return _any_subsequent_observation(growth.free_cash_flow.observations, after)
    if guidance_type is GuidanceType.MARGIN:
        return _any_subsequent_period(financial_statement_history.income_statements, after)
    if guidance_type is GuidanceType.CAPITAL_EXPENDITURE:
        return _any_subsequent_period(financial_statement_history.cash_flow_statements, after)
    return _any_subsequent_period(financial_statement_history.income_statements, after)


def extract_management_guidance(
    earnings_call: EarningsCallKnowledge,
    financial_statement_history: FinancialStatementHistory,
    growth: GrowthKnowledge,
    capital_allocation_history: CapitalAllocationHistory,
) -> "ManagementGuidanceKnowledge":
    """Pure, no I/O. `earnings_call.transcripts == ()` yields an empty
    timeline -- never a fabricated guidance history.
    `capital_allocation_history` is accepted for interface symmetry with
    Sprint 8's own `extract_management_credibility` (a future guidance
    type could reuse it) but is not read by any guidance type this
    build resolves -- see the module docstring's own closed `GuidanceType`
    -> metric mapping."""
    raw_items = _extract_raw_guidance(earnings_call)

    by_type: dict[GuidanceType, list[_RawGuidance]] = {}
    for item in raw_items:
        by_type.setdefault(item.guidance_type, []).append(item)
    for group in by_type.values():
        group.sort(key=lambda r: r.anchor)

    items: list[GuidanceItem] = []
    for group in by_type.values():
        for index, item in enumerate(group):
            previous = group[index - 1] if index > 0 else None
            is_latest = index == len(group) - 1

            outcome = _guidance_outcome(item.guidance_type, item.direction, item.anchor, financial_statement_history, growth)
            period_completed = _period_completed(item.guidance_type, item.anchor, financial_statement_history, growth)
            status = _status(item, is_latest, outcome, period_completed)
            revision_kind = _revision_kind(item, previous)

            items.append(
                GuidanceItem(
                    guidance_type=item.guidance_type, speaker=item.speaker, reporting_period=item.reporting_period,
                    statement_date=item.statement_date, fiscal_date_ending=item.fiscal_date_ending,
                    source_transcript=item.source_transcript, direction=item.direction,
                    explicit_target=item.explicit_target, explicit_target_range=item.explicit_target_range,
                    confidence_wording=item.confidence_wording, supporting_quotation=item.supporting_quotation,
                    status=status, revision_kind=revision_kind, outcome=outcome,
                )
            )

    items.sort(key=lambda g: g.statement_date)
    reliability = _reliability(tuple(items))
    return ManagementGuidanceKnowledge(guidance_items=tuple(items), reliability=reliability)


# -- Phase 7: Guidance Reliability Knowledge --------------------------------


@dataclass(frozen=True)
class GuidanceReliabilitySummary:
    """Phase 7. A pure count over the already-built guidance timeline --
    zero new computation, never a management score."""

    total_guidance_count: int
    revision_count: int
    fulfilled_count: int
    partially_fulfilled_count: int
    missed_count: int
    unresolved_count: int
    withdrawn_count: int


def _reliability(items: tuple[GuidanceItem, ...]) -> GuidanceReliabilitySummary:
    return GuidanceReliabilitySummary(
        total_guidance_count=len(items),
        revision_count=sum(1 for g in items if g.revision_kind in (RevisionKind.RAISED, RevisionKind.LOWERED, RevisionKind.REAFFIRMED, RevisionKind.UNCHANGED)),
        fulfilled_count=sum(1 for g in items if g.outcome is GuidanceOutcome.FULFILLED),
        partially_fulfilled_count=sum(1 for g in items if g.outcome is GuidanceOutcome.PARTIALLY_FULFILLED),
        missed_count=sum(1 for g in items if g.outcome is GuidanceOutcome.MISSED),
        unresolved_count=sum(1 for g in items if g.outcome is GuidanceOutcome.UNRESOLVED),
        withdrawn_count=sum(1 for g in items if g.status is GuidanceStatus.WITHDRAWN),
    )


@dataclass(frozen=True)
class ManagementGuidanceKnowledge:
    guidance_items: tuple[GuidanceItem, ...]
    """Chronological, oldest first -- the complete, immutable guidance
    timeline (Phase 3). Every prior guidance item remains present and
    unchanged even after a later item revises or withdraws it -- only
    `status`/`revision_kind` on each item's own record reflect its place
    in that timeline; no item is ever deleted or overwritten."""
    reliability: GuidanceReliabilitySummary
