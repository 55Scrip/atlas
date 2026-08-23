"""HTTP response schemas for Portfolio Decision Synthesis. Wire format
is camelCase via the shared Core `CamelModel` (ADR-004). Every field
is a direct read of an already-computed `PortfolioDecision`/
`PortfolioDecisionChange` -- nothing is recomputed or reworded here.
`DecisionAlternativeView` is reused verbatim from `atlas.alpha
.opportunity_cost.api.schemas` -- the exact same wire shape, never
redeclared.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_explanation.models import ExplanationReference
from atlas.alpha.opportunity_cost.api.schemas import DecisionAlternativeView
from atlas.alpha.portfolio_decision.models import (
    CapitalCompetition,
    PortfolioDecision,
    PortfolioDecisionChange,
    PortfolioDecisionComparison,
    PortfolioDecisionImpact,
    PortfolioDecisionReason,
    PortfolioDecisionSummary,
    PortfolioSynthesisBreakdown,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class PortfolioDecisionReferenceView(CamelModel):
    kind: str
    id: str

    @classmethod
    def from_domain(cls, reference: ExplanationReference) -> "PortfolioDecisionReferenceView":
        return cls(kind=reference.kind.value, id=reference.id)


class PortfolioDecisionReasonView(CamelModel):
    source: str
    reference: PortfolioDecisionReferenceView

    @classmethod
    def from_domain(cls, reason: PortfolioDecisionReason) -> "PortfolioDecisionReasonView":
        return cls(source=reason.source.value, reference=PortfolioDecisionReferenceView.from_domain(reason.reference))


class PortfolioDecisionImpactView(CamelModel):
    is_existing_holding: bool
    current_weight_percent: float | None
    is_largest_position: bool
    allocation_rating: str | None
    portfolio_concentration_level: str

    @classmethod
    def from_domain(cls, impact: PortfolioDecisionImpact) -> "PortfolioDecisionImpactView":
        return cls(
            is_existing_holding=impact.is_existing_holding,
            current_weight_percent=impact.current_weight_percent,
            is_largest_position=impact.is_largest_position,
            allocation_rating=impact.allocation_rating,
            portfolio_concentration_level=impact.portfolio_concentration_level.value,
        )


class CapitalCompetitionView(CamelModel):
    case_id: str
    competing_alternatives: list[DecisionAlternativeView]
    non_competing_alternatives: list[DecisionAlternativeView]

    @classmethod
    def from_domain(cls, competition: CapitalCompetition) -> "CapitalCompetitionView":
        return cls(
            case_id=competition.case_id,
            competing_alternatives=[DecisionAlternativeView.from_domain(a) for a in competition.competing_alternatives],
            non_competing_alternatives=[DecisionAlternativeView.from_domain(a) for a in competition.non_competing_alternatives],
        )


class PortfolioDecisionView(CamelModel):
    case_id: str
    action: str
    category: str
    impact: PortfolioDecisionImpactView
    capital_competition: CapitalCompetitionView
    supporting_reasons: list[PortfolioDecisionReasonView]
    limiting_reasons: list[PortfolioDecisionReasonView]
    primary_limiting_reason: PortfolioDecisionReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, decision: PortfolioDecision) -> "PortfolioDecisionView":
        return cls(
            case_id=decision.case_id,
            action=decision.action.value,
            category=decision.category.value,
            impact=PortfolioDecisionImpactView.from_domain(decision.impact),
            capital_competition=CapitalCompetitionView.from_domain(decision.capital_competition),
            supporting_reasons=[PortfolioDecisionReasonView.from_domain(r) for r in decision.supporting_reasons],
            limiting_reasons=[PortfolioDecisionReasonView.from_domain(r) for r in decision.limiting_reasons],
            primary_limiting_reason=PortfolioDecisionReasonView.from_domain(decision.primary_limiting_reason)
            if decision.primary_limiting_reason is not None
            else None,
            generated_at=decision.generated_at,
        )


class PortfolioDecisionSummaryView(CamelModel):
    case_id: str
    action: str
    category: str
    primary_limiting_reason: PortfolioDecisionReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: PortfolioDecisionSummary) -> "PortfolioDecisionSummaryView":
        return cls(
            case_id=summary.case_id,
            action=summary.action.value,
            category=summary.category.value,
            primary_limiting_reason=PortfolioDecisionReasonView.from_domain(summary.primary_limiting_reason)
            if summary.primary_limiting_reason is not None
            else None,
            generated_at=summary.generated_at,
        )


class PortfolioDecisionChangeView(CamelModel):
    case_id: str
    previous_category: str
    current_category: str
    competition_changed: bool
    new_limiting: list[PortfolioDecisionReasonView]
    resolved_limiting: list[PortfolioDecisionReasonView]
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: PortfolioDecisionChange) -> "PortfolioDecisionChangeView":
        return cls(
            case_id=change.case_id,
            previous_category=change.previous_category.value,
            current_category=change.current_category.value,
            competition_changed=change.competition_changed,
            new_limiting=[PortfolioDecisionReasonView.from_domain(r) for r in change.new_limiting],
            resolved_limiting=[PortfolioDecisionReasonView.from_domain(r) for r in change.resolved_limiting],
            detected_at=change.detected_at,
        )


class PortfolioDecisionComparisonView(CamelModel):
    a: PortfolioDecisionView
    b: PortfolioDecisionView
    better_portfolio_fit_case_id: str | None
    shared_strengths: list[PortfolioDecisionReferenceView]
    shared_weaknesses: list[PortfolioDecisionReferenceView]
    shared_competitor_case_ids: list[str]

    @classmethod
    def from_domain(cls, comparison: PortfolioDecisionComparison) -> "PortfolioDecisionComparisonView":
        return cls(
            a=PortfolioDecisionView.from_domain(comparison.a),
            b=PortfolioDecisionView.from_domain(comparison.b),
            better_portfolio_fit_case_id=comparison.better_portfolio_fit_case_id,
            shared_strengths=[PortfolioDecisionReferenceView.from_domain(r) for r in comparison.shared_strengths],
            shared_weaknesses=[PortfolioDecisionReferenceView.from_domain(r) for r in comparison.shared_weaknesses],
            shared_competitor_case_ids=list(comparison.shared_competitor_case_ids),
        )


class PortfolioSynthesisBreakdownView(CamelModel):
    supports_portfolio: list[str]
    highest_capital_competition: list[str]
    conflicts_with_portfolio: list[str]
    neutral: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioSynthesisBreakdown) -> "PortfolioSynthesisBreakdownView":
        return cls(
            supports_portfolio=list(breakdown.supports_portfolio),
            highest_capital_competition=list(breakdown.highest_capital_competition),
            conflicts_with_portfolio=list(breakdown.conflicts_with_portfolio),
            neutral=list(breakdown.neutral),
        )
