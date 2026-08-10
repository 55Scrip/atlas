"""HTTP response schemas for History v1. Wire format is camelCase via
the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module. Reuses `ChangeFindingView` from `atlas.alpha
.investment_case.api.schemas` directly for the `changes` field -- the
identical wire shape for the identical underlying
`investment_case_change.ChangeFinding`, never redefined.

Every field here is a direct read of an already-persisted
`AnalyticalSnapshot`/`ChangeIntelligence` pair (see this package's own
`__init__.py`) -- nothing is recomputed. `snapshot_id` is the one field
with no direct domain counterpart: `AnalyticalSnapshot` itself carries
no synthetic id (the repository keys rows by `(case_id, captured_at)`
alone), so it is derived here, at the wire boundary only, as
`f"{case_id}:{captured_at.isoformat()}"` -- stable and unique per row,
used by the frontend purely as a React key / expand-state key, never
interpreted as a real persistence identifier.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.investment_case.api.schemas import ChangeFindingView
from atlas.analysis_engine.investment_case_history import AnalyticalHistory, HistoricalAnalysisEntry
from atlas.core.infrastructure.api.serialization import CamelModel


class BusinessCategoryStateView(CamelModel):
    category: str
    status: str
    finding_id: str


class RiskCategoryStateView(CamelModel):
    category: str
    status: str
    finding_id: str


class HistoricalAnalysisEntryView(CamelModel):
    """One Case's own persisted analytical state at one point in time,
    plus the (persisted, never recomputed) `ChangeIntelligence`
    describing how it differs from the entry immediately before it for
    the same Case. Product-language field names throughout -- no
    `AnalyticalSnapshot`/`ChangeFinding`/`content_hash`/
    `BusinessCategoryStatus` vocabulary leaks past this schema."""

    case_id: str
    ticker: str | None
    snapshot_id: str
    captured_at: datetime
    is_baseline: bool
    thesis_impact: str
    summary: str
    change_count: int
    changes: list[ChangeFindingView]
    atlas_thesis_narrative: str | None
    atlas_thesis_posture: str | None
    strengths: list[str]
    risks: list[str]
    open_questions: list[str]
    business_category_states: list[BusinessCategoryStateView]
    risk_category_states: list[RiskCategoryStateView]
    valuation_status: str
    current_yield: float | None

    @classmethod
    def from_domain(cls, entry: HistoricalAnalysisEntry) -> "HistoricalAnalysisEntryView":
        snapshot = entry.snapshot
        change_intelligence = entry.change_intelligence
        return cls(
            case_id=entry.case_id,
            ticker=entry.ticker,
            snapshot_id=f"{entry.case_id}:{snapshot.captured_at.isoformat()}",
            captured_at=snapshot.captured_at,
            is_baseline=change_intelligence.is_baseline,
            thesis_impact=change_intelligence.thesis_impact.value,
            summary=change_intelligence.summary_narrative,
            change_count=len(change_intelligence.changes),
            changes=[ChangeFindingView.from_domain(c) for c in change_intelligence.changes],
            atlas_thesis_narrative=snapshot.atlas_thesis_narrative,
            atlas_thesis_posture=snapshot.atlas_thesis_posture,
            strengths=list(snapshot.strength_kinds),
            risks=list(snapshot.risk_highlight_kinds),
            open_questions=list(snapshot.open_question_origins),
            business_category_states=[
                BusinessCategoryStateView(category=category, status=status, finding_id=finding_id)
                for category, status, finding_id in snapshot.business_category_states
            ],
            risk_category_states=[
                RiskCategoryStateView(category=category, status=status, finding_id=finding_id)
                for category, status, finding_id in snapshot.risk_category_states
            ],
            valuation_status=snapshot.valuation_status,
            current_yield=snapshot.current_yield,
        )


class AnalyticalHistoryView(CamelModel):
    generated_at: datetime
    entries: list[HistoricalAnalysisEntryView]

    @classmethod
    def from_domain(cls, history: AnalyticalHistory) -> "AnalyticalHistoryView":
        return cls(
            generated_at=history.generated_at,
            entries=[HistoricalAnalysisEntryView.from_domain(e) for e in history.entries],
        )
