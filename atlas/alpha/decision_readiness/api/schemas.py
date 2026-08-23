"""HTTP response schemas for Decision Readiness. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004). Every field is a
direct read of an already-computed `DecisionReadiness`/comparison --
nothing is recomputed or reworded here."""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionReadiness,
    DecisionReadinessChange,
    DecisionReadinessComparison,
    DecisionReadinessReason,
    DecisionReadinessStatus,
    DecisionReadinessSummary,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class DecisionBlockerView(CamelModel):
    kind: str
    detail: int | None

    @classmethod
    def from_domain(cls, blocker: DecisionBlocker) -> "DecisionBlockerView":
        return cls(kind=blocker.kind.value, detail=blocker.detail)


class DecisionReadinessReasonView(CamelModel):
    kind: str
    detail: int | None

    @classmethod
    def from_domain(cls, reason: DecisionReadinessReason) -> "DecisionReadinessReasonView":
        return cls(kind=reason.kind.value, detail=reason.detail)


class DecisionReadinessView(CamelModel):
    case_id: str
    status: str
    blockers: list[DecisionBlockerView]
    supporting_reasons: list[DecisionReadinessReasonView]
    generated_at: datetime

    @classmethod
    def from_domain(cls, readiness: DecisionReadiness) -> "DecisionReadinessView":
        return cls(
            case_id=readiness.case_id,
            status=readiness.status.value,
            blockers=[DecisionBlockerView.from_domain(b) for b in readiness.blockers],
            supporting_reasons=[DecisionReadinessReasonView.from_domain(r) for r in readiness.supporting_reasons],
            generated_at=readiness.generated_at,
        )


class DecisionReadinessSummaryView(CamelModel):
    case_id: str
    status: str
    primary_blocker: DecisionBlockerView | None
    primary_supporting_reason: DecisionReadinessReasonView | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, summary: DecisionReadinessSummary) -> "DecisionReadinessSummaryView":
        return cls(
            case_id=summary.case_id,
            status=summary.status.value,
            primary_blocker=DecisionBlockerView.from_domain(summary.primary_blocker)
            if summary.primary_blocker is not None
            else None,
            primary_supporting_reason=DecisionReadinessReasonView.from_domain(summary.primary_supporting_reason)
            if summary.primary_supporting_reason is not None
            else None,
            generated_at=summary.generated_at,
        )


class DecisionReadinessComparisonView(CamelModel):
    a: DecisionReadinessView
    b: DecisionReadinessView
    closer_case_id: str | None
    differing_blocker_kinds: list[str]

    @classmethod
    def from_domain(cls, comparison: DecisionReadinessComparison) -> "DecisionReadinessComparisonView":
        return cls(
            a=DecisionReadinessView.from_domain(comparison.a),
            b=DecisionReadinessView.from_domain(comparison.b),
            closer_case_id=comparison.closer_case_id,
            differing_blocker_kinds=[k.value for k in comparison.differing_blocker_kinds],
        )


class DecisionReadinessChangeView(CamelModel):
    case_id: str
    previous_status: str
    current_status: str
    new_blockers: list[str]
    resolved_blockers: list[str]
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: DecisionReadinessChange) -> "DecisionReadinessChangeView":
        return cls(
            case_id=change.case_id,
            previous_status=change.previous_status.value,
            current_status=change.current_status.value,
            new_blockers=[k.value for k in change.new_blockers],
            resolved_blockers=[k.value for k in change.resolved_blockers],
            detected_at=change.detected_at,
        )


class PortfolioReadinessBreakdownView(CamelModel):
    """Deliverable 7 -- ticker lists only, grouped by status; never a
    ranking within a group."""

    ready: list[str]
    almost_ready: list[str]
    waiting: list[str]
    blocked: list[str]
    unavailable: list[str]
    unknown: list[str]

    @classmethod
    def from_domain(cls, buckets: dict[DecisionReadinessStatus, tuple[str, ...]]) -> "PortfolioReadinessBreakdownView":
        return cls(
            ready=list(buckets.get(DecisionReadinessStatus.READY, ())),
            almost_ready=list(buckets.get(DecisionReadinessStatus.ALMOST_READY, ())),
            waiting=list(buckets.get(DecisionReadinessStatus.WAITING, ())),
            blocked=list(buckets.get(DecisionReadinessStatus.BLOCKED, ())),
            unavailable=list(buckets.get(DecisionReadinessStatus.UNAVAILABLE, ())),
            unknown=list(buckets.get(DecisionReadinessStatus.UNKNOWN, ())),
        )
