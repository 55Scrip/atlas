"""HTTP response schemas for Decision Memory. Wire format is camelCase
via the shared Core `CamelModel` (ADR-004). Every field is a direct
read of an already-persisted `DecisionSnapshot`/`DecisionMemoryChange` --
nothing is recomputed or reworded here.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_memory.models import (
    DecisionMemoryChange,
    DecisionMemory,
    DecisionMemoryComparison,
    DecisionSnapshot,
    DecisionTimeline,
    DecisionTimelineEntry,
    PortfolioDecisionMemoryBreakdown,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class DecisionSnapshotView(CamelModel):
    case_id: str
    action: str
    readiness_status: str
    blocker_codes: list[str]
    conviction_strength: str
    conviction_stability: str
    decision_path_step_count: int
    decision_path_final_state: str
    primary_alternative_kind: str | None
    alternative_count: int
    content_hash: str
    recorded_at: datetime

    @classmethod
    def from_domain(cls, snapshot: DecisionSnapshot) -> "DecisionSnapshotView":
        return cls(
            case_id=snapshot.case_id,
            action=snapshot.action.value,
            readiness_status=snapshot.readiness_status.value,
            blocker_codes=list(snapshot.blocker_codes),
            conviction_strength=snapshot.conviction_strength.value,
            conviction_stability=snapshot.conviction_stability.value,
            decision_path_step_count=snapshot.decision_path_step_count,
            decision_path_final_state=snapshot.decision_path_final_state.value,
            primary_alternative_kind=snapshot.primary_alternative_kind.value if snapshot.primary_alternative_kind is not None else None,
            alternative_count=snapshot.alternative_count,
            content_hash=snapshot.content_hash,
            recorded_at=snapshot.recorded_at,
        )


class DecisionMemoryChangeView(CamelModel):
    case_id: str
    is_baseline: bool
    previous_action: str | None
    current_action: str
    recommendation_changed: bool
    conviction_direction: str | None
    readiness_direction: str | None
    decision_path_direction: str | None
    blockers_resolved: list[str]
    blockers_added: list[str]
    alternative_changed: bool
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: DecisionMemoryChange) -> "DecisionMemoryChangeView":
        return cls(
            case_id=change.case_id,
            is_baseline=change.is_baseline,
            previous_action=change.previous_action.value if change.previous_action is not None else None,
            current_action=change.current_action.value,
            recommendation_changed=change.recommendation_changed,
            conviction_direction=change.conviction_direction.value if change.conviction_direction is not None else None,
            readiness_direction=change.readiness_direction.value if change.readiness_direction is not None else None,
            decision_path_direction=change.decision_path_direction.value if change.decision_path_direction is not None else None,
            blockers_resolved=list(change.blockers_resolved),
            blockers_added=list(change.blockers_added),
            alternative_changed=change.alternative_changed,
            detected_at=change.detected_at,
        )


class DecisionTimelineEntryView(CamelModel):
    snapshot: DecisionSnapshotView
    change: DecisionMemoryChangeView

    @classmethod
    def from_domain(cls, entry: DecisionTimelineEntry) -> "DecisionTimelineEntryView":
        return cls(snapshot=DecisionSnapshotView.from_domain(entry.snapshot), change=DecisionMemoryChangeView.from_domain(entry.change))


class DecisionTimelineView(CamelModel):
    case_id: str
    entries: list[DecisionTimelineEntryView]

    @classmethod
    def from_domain(cls, timeline: DecisionTimeline) -> "DecisionTimelineView":
        return cls(case_id=timeline.case_id, entries=[DecisionTimelineEntryView.from_domain(e) for e in timeline.entries])


class DecisionMemoryView(CamelModel):
    case_id: str
    current_snapshot: DecisionSnapshotView
    previous_snapshot: DecisionSnapshotView | None
    latest_change: DecisionMemoryChangeView | None
    history: DecisionTimelineView

    @classmethod
    def from_domain(cls, memory: DecisionMemory) -> "DecisionMemoryView":
        return cls(
            case_id=memory.case_id,
            current_snapshot=DecisionSnapshotView.from_domain(memory.current_snapshot),
            previous_snapshot=DecisionSnapshotView.from_domain(memory.previous_snapshot) if memory.previous_snapshot is not None else None,
            latest_change=DecisionMemoryChangeView.from_domain(memory.latest_change) if memory.latest_change is not None else None,
            history=DecisionTimelineView.from_domain(memory.history),
        )


class DecisionMemoryComparisonView(CamelModel):
    a: DecisionMemoryView
    b: DecisionMemoryView
    more_recently_changed_case_id: str | None
    more_stable_case_id: str | None
    conviction_changed_case_id: str | None
    blockers_disappeared_case_id: str | None

    @classmethod
    def from_domain(cls, comparison: DecisionMemoryComparison) -> "DecisionMemoryComparisonView":
        return cls(
            a=DecisionMemoryView.from_domain(comparison.a),
            b=DecisionMemoryView.from_domain(comparison.b),
            more_recently_changed_case_id=comparison.more_recently_changed_case_id,
            more_stable_case_id=comparison.more_stable_case_id,
            conviction_changed_case_id=comparison.conviction_changed_case_id,
            blockers_disappeared_case_id=comparison.blockers_disappeared_case_id,
        )


class PortfolioDecisionMemoryBreakdownView(CamelModel):
    """Deliverable 7 -- ticker lists only, in holdings order; never a
    ranking."""

    recently_changed: list[str]
    stable: list[str]
    recently_strengthened: list[str]
    recently_weakened: list[str]

    @classmethod
    def from_domain(cls, breakdown: PortfolioDecisionMemoryBreakdown) -> "PortfolioDecisionMemoryBreakdownView":
        return cls(
            recently_changed=list(breakdown.recently_changed),
            stable=list(breakdown.stable),
            recently_strengthened=list(breakdown.recently_strengthened),
            recently_weakened=list(breakdown.recently_weakened),
        )
