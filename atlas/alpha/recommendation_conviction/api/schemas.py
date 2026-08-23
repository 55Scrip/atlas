"""HTTP response schemas for Recommendation Conviction & Strength. Wire
format is camelCase via the shared Core `CamelModel` (ADR-004). Every
field is a direct read of an already-computed `RecommendationConviction`/
comparison -- nothing is recomputed or reworded here."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.recommendation_conviction.models import (
    ConvictionChange,
    ConvictionComparison,
    ConvictionReason,
    ConvictionSummary,
    PortfolioConvictionBreakdown,
    RecommendationConviction,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class ConvictionReasonView(CamelModel):
    source: str
    code: str

    @classmethod
    def from_domain(cls, reason: ConvictionReason) -> "ConvictionReasonView":
        return cls(source=reason.source.value, code=reason.code)


class RecommendationConvictionView(CamelModel):
    case_id: str
    action: str
    strength: str
    stability: str
    supporting_reasons: list[ConvictionReasonView]
    limiting_reasons: list[ConvictionReasonView]
    strengthening_trigger: ConvictionReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, conviction: RecommendationConviction) -> "RecommendationConvictionView":
        return cls(
            case_id=conviction.case_id,
            action=conviction.action.value,
            strength=conviction.strength.value,
            stability=conviction.stability.value,
            supporting_reasons=[ConvictionReasonView.from_domain(r) for r in conviction.supporting_reasons],
            limiting_reasons=[ConvictionReasonView.from_domain(r) for r in conviction.limiting_reasons],
            strengthening_trigger=ConvictionReasonView.from_domain(conviction.strengthening_trigger)
            if conviction.strengthening_trigger is not None
            else None,
            generated_at=conviction.generated_at,
        )


class ConvictionSummaryView(CamelModel):
    case_id: str
    action: str
    strength: str
    stability: str
    primary_supporting_reason: ConvictionReasonView | None
    primary_limiting_reason: ConvictionReasonView | None
    strengthening_trigger: ConvictionReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: ConvictionSummary) -> "ConvictionSummaryView":
        return cls(
            case_id=summary.case_id,
            action=summary.action.value,
            strength=summary.strength.value,
            stability=summary.stability.value,
            primary_supporting_reason=ConvictionReasonView.from_domain(summary.primary_supporting_reason)
            if summary.primary_supporting_reason is not None
            else None,
            primary_limiting_reason=ConvictionReasonView.from_domain(summary.primary_limiting_reason)
            if summary.primary_limiting_reason is not None
            else None,
            strengthening_trigger=ConvictionReasonView.from_domain(summary.strengthening_trigger)
            if summary.strengthening_trigger is not None
            else None,
            generated_at=summary.generated_at,
        )


class ConvictionComparisonView(CamelModel):
    a: RecommendationConvictionView
    b: RecommendationConvictionView
    stronger_case_id: str | None
    more_evidence_limited_case_id: str | None
    more_operationally_blocked_case_id: str | None
    more_stable_case_id: str | None

    @classmethod
    def from_domain(cls, comparison: ConvictionComparison) -> "ConvictionComparisonView":
        return cls(
            a=RecommendationConvictionView.from_domain(comparison.a),
            b=RecommendationConvictionView.from_domain(comparison.b),
            stronger_case_id=comparison.stronger_case_id,
            more_evidence_limited_case_id=comparison.more_evidence_limited_case_id,
            more_operationally_blocked_case_id=comparison.more_operationally_blocked_case_id,
            more_stable_case_id=comparison.more_stable_case_id,
        )


class ConvictionChangeView(CamelModel):
    case_id: str
    previous_strength: str
    current_strength: str
    previous_stability: str
    current_stability: str
    new_limiting_reasons: list[ConvictionReasonView]
    resolved_limiting_reasons: list[ConvictionReasonView]
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: ConvictionChange) -> "ConvictionChangeView":
        return cls(
            case_id=change.case_id,
            previous_strength=change.previous_strength.value,
            current_strength=change.current_strength.value,
            previous_stability=change.previous_stability.value,
            current_stability=change.current_stability.value,
            new_limiting_reasons=[ConvictionReasonView.from_domain(r) for r in change.new_limiting_reasons],
            resolved_limiting_reasons=[ConvictionReasonView.from_domain(r) for r in change.resolved_limiting_reasons],
            detected_at=change.detected_at,
        )


class PortfolioConvictionBreakdownView(CamelModel):
    """Deliverable 7 -- ticker lists only, in holdings order; never a
    ranking, never an allocation suggestion."""

    highest_conviction: list[str]
    lowest_conviction: list[str]
    evidence_limited: list[str]
    operationally_blocked: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioConvictionBreakdown) -> "PortfolioConvictionBreakdownView":
        return cls(
            highest_conviction=list(breakdown.highest_conviction),
            lowest_conviction=list(breakdown.lowest_conviction),
            evidence_limited=list(breakdown.evidence_limited),
            operationally_blocked=list(breakdown.operationally_blocked),
        )
