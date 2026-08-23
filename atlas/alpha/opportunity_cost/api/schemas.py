"""HTTP response schemas for Decision Alternatives & Opportunity Cost.
Wire format is camelCase via the shared Core `CamelModel` (ADR-004).
Every field is a direct read of an already-computed `OpportunityCost`/
comparison -- nothing is recomputed or reworded here.

**`AlternativeComparisonView` reuses Sprint 2's and Sprint 3's own
already-real wire views verbatim** (`ConvictionComparisonView`,
`DecisionPathComparisonView`) -- their own `from_domain` classmethods,
never re-derived here.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_path.api.schemas import DecisionPathComparisonView
from atlas.alpha.opportunity_cost.models import (
    AlternativeComparison,
    AlternativeReason,
    DecisionAlternative,
    DecisionAlternativeSummary,
    DecisionTradeoff,
    OpportunityCost,
    OpportunityCostChange,
    PortfolioOpportunityCostBreakdown,
)
from atlas.alpha.recommendation_conviction.api.schemas import ConvictionComparisonView
from atlas.core.infrastructure.api.serialization import CamelModel


class AlternativeReasonView(CamelModel):
    source: str
    code: str

    @classmethod
    def from_domain(cls, reason: AlternativeReason) -> "AlternativeReasonView":
        return cls(source=reason.source.value, code=reason.code)


class DecisionAlternativeView(CamelModel):
    kind: str
    case_id: str | None
    ticker: str | None
    action: str | None
    strength: str | None
    reason: AlternativeReasonView

    @classmethod
    def from_domain(cls, alternative: DecisionAlternative) -> "DecisionAlternativeView":
        return cls(
            kind=alternative.kind.value,
            case_id=alternative.case_id,
            ticker=alternative.ticker,
            action=alternative.action.value if alternative.action is not None else None,
            strength=alternative.strength.value if alternative.strength is not None else None,
            reason=AlternativeReasonView.from_domain(alternative.reason),
        )


class AlternativeComparisonView(CamelModel):
    conviction: ConvictionComparisonView
    path: DecisionPathComparisonView
    more_dependency_blocked_case_id: str | None

    @classmethod
    def from_domain(cls, comparison: AlternativeComparison) -> "AlternativeComparisonView":
        return cls(
            conviction=ConvictionComparisonView.from_domain(comparison.conviction),
            path=DecisionPathComparisonView.from_domain(comparison.path),
            more_dependency_blocked_case_id=comparison.more_dependency_blocked_case_id,
        )


class DecisionTradeoffView(CamelModel):
    alternative: DecisionAlternativeView
    comparison: AlternativeComparisonView | None

    @classmethod
    def from_domain(cls, tradeoff: DecisionTradeoff) -> "DecisionTradeoffView":
        return cls(
            alternative=DecisionAlternativeView.from_domain(tradeoff.alternative),
            comparison=AlternativeComparisonView.from_domain(tradeoff.comparison) if tradeoff.comparison is not None else None,
        )


class OpportunityCostView(CamelModel):
    case_id: str
    current_action: str
    tradeoffs: list[DecisionTradeoffView]
    generated_at: datetime

    @classmethod
    def from_domain(cls, opportunity_cost: OpportunityCost) -> "OpportunityCostView":
        return cls(
            case_id=opportunity_cost.case_id,
            current_action=opportunity_cost.current_action.value,
            tradeoffs=[DecisionTradeoffView.from_domain(t) for t in opportunity_cost.tradeoffs],
            generated_at=opportunity_cost.generated_at,
        )


class DecisionAlternativeSummaryView(CamelModel):
    case_id: str
    current_action: str
    primary_alternative: DecisionAlternativeView | None
    alternative_count: int
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: DecisionAlternativeSummary) -> "DecisionAlternativeSummaryView":
        return cls(
            case_id=summary.case_id,
            current_action=summary.current_action.value,
            primary_alternative=DecisionAlternativeView.from_domain(summary.primary_alternative)
            if summary.primary_alternative is not None
            else None,
            alternative_count=summary.alternative_count,
            generated_at=summary.generated_at,
        )


class OpportunityCostChangeView(CamelModel):
    case_id: str
    new_alternatives: list[DecisionAlternativeView]
    disappeared_alternatives: list[DecisionAlternativeView]
    strengthened_alternatives: list[DecisionAlternativeView]
    weakened_alternatives: list[DecisionAlternativeView]
    primary_alternative_changed: bool
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: OpportunityCostChange) -> "OpportunityCostChangeView":
        return cls(
            case_id=change.case_id,
            new_alternatives=[DecisionAlternativeView.from_domain(a) for a in change.new_alternatives],
            disappeared_alternatives=[DecisionAlternativeView.from_domain(a) for a in change.disappeared_alternatives],
            strengthened_alternatives=[DecisionAlternativeView.from_domain(a) for a in change.strengthened_alternatives],
            weakened_alternatives=[DecisionAlternativeView.from_domain(a) for a in change.weakened_alternatives],
            primary_alternative_changed=change.primary_alternative_changed,
            detected_at=change.detected_at,
        )


class PortfolioOpportunityCostBreakdownView(CamelModel):
    """Deliverable 7 -- ticker lists only, in holdings order; never a
    ranking, never an allocation suggestion."""

    holdings_competing_for_capital: list[str]
    watchlist_competing_with_holdings: list[str]
    waiting_preferable: list[str]
    no_action_appropriate: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioOpportunityCostBreakdown) -> "PortfolioOpportunityCostBreakdownView":
        return cls(
            holdings_competing_for_capital=list(breakdown.holdings_competing_for_capital),
            watchlist_competing_with_holdings=list(breakdown.watchlist_competing_with_holdings),
            waiting_preferable=list(breakdown.waiting_preferable),
            no_action_appropriate=list(breakdown.no_action_appropriate),
        )
