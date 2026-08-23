"""HTTP response schemas for Decision Reliability. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004). Every field is a
direct read of an already-computed `DecisionReliability`/
`ReliabilityChange` -- nothing is recomputed or reworded here.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_explanation.models import ExplanationReference
from atlas.alpha.decision_reliability.models import (
    DecisionReliability,
    DecisionReliabilitySummary,
    PortfolioReliabilityBreakdown,
    ReliabilityChange,
    ReliabilityComparison,
    ReliabilityReason,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class ReliabilityReferenceView(CamelModel):
    kind: str
    id: str

    @classmethod
    def from_domain(cls, reference: ExplanationReference) -> "ReliabilityReferenceView":
        return cls(kind=reference.kind.value, id=reference.id)


class ReliabilityReasonView(CamelModel):
    source: str
    reference: ReliabilityReferenceView
    count: int | None
    total: int | None

    @classmethod
    def from_domain(cls, reason: ReliabilityReason) -> "ReliabilityReasonView":
        return cls(
            source=reason.source.value,
            reference=ReliabilityReferenceView.from_domain(reason.reference),
            count=reason.count,
            total=reason.total,
        )


class DecisionReliabilityView(CamelModel):
    case_id: str
    level: str
    supporting_reasons: list[ReliabilityReasonView]
    limiting_reasons: list[ReliabilityReasonView]
    primary_limiting_reason: ReliabilityReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, reliability: DecisionReliability) -> "DecisionReliabilityView":
        return cls(
            case_id=reliability.case_id,
            level=reliability.level.value,
            supporting_reasons=[ReliabilityReasonView.from_domain(r) for r in reliability.supporting_reasons],
            limiting_reasons=[ReliabilityReasonView.from_domain(r) for r in reliability.limiting_reasons],
            primary_limiting_reason=ReliabilityReasonView.from_domain(reliability.primary_limiting_reason)
            if reliability.primary_limiting_reason is not None
            else None,
            generated_at=reliability.generated_at,
        )


class DecisionReliabilitySummaryView(CamelModel):
    case_id: str
    level: str
    primary_limiting_reason: ReliabilityReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: DecisionReliabilitySummary) -> "DecisionReliabilitySummaryView":
        return cls(
            case_id=summary.case_id,
            level=summary.level.value,
            primary_limiting_reason=ReliabilityReasonView.from_domain(summary.primary_limiting_reason)
            if summary.primary_limiting_reason is not None
            else None,
            generated_at=summary.generated_at,
        )


class ReliabilityChangeView(CamelModel):
    case_id: str
    previous_level: str
    current_level: str
    direction: str | None
    new_limiting: list[ReliabilityReasonView]
    resolved_limiting: list[ReliabilityReasonView]
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: ReliabilityChange) -> "ReliabilityChangeView":
        return cls(
            case_id=change.case_id,
            previous_level=change.previous_level.value,
            current_level=change.current_level.value,
            direction=change.direction.value if change.direction is not None else None,
            new_limiting=[ReliabilityReasonView.from_domain(r) for r in change.new_limiting],
            resolved_limiting=[ReliabilityReasonView.from_domain(r) for r in change.resolved_limiting],
            detected_at=change.detected_at,
        )


class ReliabilityComparisonView(CamelModel):
    a: DecisionReliabilityView
    b: DecisionReliabilityView
    more_reliable_case_id: str | None
    shared_limiting: list[ReliabilityReferenceView]
    differing_limiting_a: list[ReliabilityReferenceView]
    differing_limiting_b: list[ReliabilityReferenceView]
    shared_supporting: list[ReliabilityReferenceView]

    @classmethod
    def from_domain(cls, comparison: ReliabilityComparison) -> "ReliabilityComparisonView":
        return cls(
            a=DecisionReliabilityView.from_domain(comparison.a),
            b=DecisionReliabilityView.from_domain(comparison.b),
            more_reliable_case_id=comparison.more_reliable_case_id,
            shared_limiting=[ReliabilityReferenceView.from_domain(r) for r in comparison.shared_limiting],
            differing_limiting_a=[ReliabilityReferenceView.from_domain(r) for r in comparison.differing_limiting_a],
            differing_limiting_b=[ReliabilityReferenceView.from_domain(r) for r in comparison.differing_limiting_b],
            shared_supporting=[ReliabilityReferenceView.from_domain(r) for r in comparison.shared_supporting],
        )


class PortfolioReliabilityBreakdownView(CamelModel):
    most_reliable: list[str]
    least_reliable: list[str]
    recently_improved: list[str]
    recently_weakened: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioReliabilityBreakdown) -> "PortfolioReliabilityBreakdownView":
        return cls(
            most_reliable=list(breakdown.most_reliable),
            least_reliable=list(breakdown.least_reliable),
            recently_improved=list(breakdown.recently_improved),
            recently_weakened=list(breakdown.recently_weakened),
        )
