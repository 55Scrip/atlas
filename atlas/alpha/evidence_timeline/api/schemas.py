"""HTTP response schemas for the Evidence Timeline API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module. Every field here is a direct read of an
already-persisted `EvidenceSnapshot`/`EvidenceHistory` pair -- nothing
is recomputed, mirroring `investment_case_history.api.schemas`'s own
module docstring.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.evidence_timeline.engine import is_material_transition
from atlas.alpha.evidence_timeline.models import EvidenceHistory, EvidenceSnapshot, EvidenceTransition, SourceEvidenceEvent
from atlas.alpha.evidence_timeline.service import EvidenceTimelineEntry, EvidenceTimelineFeed
from atlas.core.infrastructure.api.serialization import CamelModel


class EvidenceTransitionView(CamelModel):
    id: str
    category: str
    direction: str
    previous_state: str
    current_state: str
    is_material: bool

    @classmethod
    def from_domain(cls, transition: EvidenceTransition) -> "EvidenceTransitionView":
        return cls(
            id=transition.id,
            category=transition.category.value,
            direction=transition.direction.value,
            previous_state=transition.previous_state,
            current_state=transition.current_state,
            is_material=is_material_transition(transition),
        )


class SourceEvidenceEventView(CamelModel):
    """**Source Evidence History** -- a real `(fact_kind, period)`
    combination new since the last capture, deliberately never merged
    with `EvidenceTransitionView` (**Atlas Analysis History**)."""

    fact_kind: str
    period: str

    @classmethod
    def from_domain(cls, event: SourceEvidenceEvent) -> "SourceEvidenceEventView":
        return cls(fact_kind=event.fact_kind, period=event.period)


class EvidenceSnapshotView(CamelModel):
    overall_coverage: str
    overall_confidence: str
    stance_level: str | None
    evidence_quality: str
    conflict_status: str
    freshness: str
    missing_dimensions: list[str]
    captured_at: datetime

    @classmethod
    def from_domain(cls, snapshot: EvidenceSnapshot) -> "EvidenceSnapshotView":
        return cls(
            overall_coverage=snapshot.overall_coverage,
            overall_confidence=snapshot.overall_confidence,
            stance_level=snapshot.stance_level,
            evidence_quality=snapshot.evidence_quality,
            conflict_status=snapshot.conflict_status,
            freshness=snapshot.freshness,
            missing_dimensions=list(snapshot.missing_dimensions),
            captured_at=snapshot.captured_at,
        )


class EvidenceHistoryView(CamelModel):
    is_baseline: bool
    transitions: list[EvidenceTransitionView]
    new_source_evidence: list[SourceEvidenceEventView]
    previous_captured_at: datetime | None
    current_captured_at: datetime

    @classmethod
    def from_domain(cls, history: EvidenceHistory) -> "EvidenceHistoryView":
        return cls(
            is_baseline=history.is_baseline,
            transitions=[EvidenceTransitionView.from_domain(t) for t in history.transitions],
            new_source_evidence=[SourceEvidenceEventView.from_domain(e) for e in history.new_source_evidence],
            previous_captured_at=history.previous_captured_at,
            current_captured_at=history.current_captured_at,
        )


class EvidenceTimelineEntryPairView(CamelModel):
    """One row of `EvidenceTimelineService.history_for_case`/
    `.history_for_ticker` -- a snapshot paired with its own transition,
    oldest first."""

    snapshot: EvidenceSnapshotView
    history: EvidenceHistoryView


class EvidenceTimelineEntryView(CamelModel):
    case_id: str
    ticker: str | None
    snapshot: EvidenceSnapshotView
    history: EvidenceHistoryView

    @classmethod
    def from_domain(cls, entry: EvidenceTimelineEntry) -> "EvidenceTimelineEntryView":
        return cls(
            case_id=entry.case_id,
            ticker=entry.ticker,
            snapshot=EvidenceSnapshotView.from_domain(entry.snapshot),
            history=EvidenceHistoryView.from_domain(entry.history),
        )


class EvidenceTimelineFeedView(CamelModel):
    generated_at: datetime
    entries: list[EvidenceTimelineEntryView]

    @classmethod
    def from_domain(cls, feed: EvidenceTimelineFeed) -> "EvidenceTimelineFeedView":
        return cls(generated_at=feed.generated_at, entries=[EvidenceTimelineEntryView.from_domain(e) for e in feed.entries])
