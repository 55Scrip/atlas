"""HTTP response schemas for Daily Brief v1. Wire format is camelCase
via the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module. Reuses `ChangeFindingView` from `atlas.alpha
.investment_case.api.schemas` directly for the `changes` field -- the
identical wire shape for the identical underlying
`investment_case_change.ChangeFinding`, never redefined.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.investment_case.api.schemas import ChangeFindingView
from atlas.analysis_engine.daily_brief import DailyBrief, DailyBriefEntry
from atlas.core.infrastructure.api.serialization import CamelModel


class DailyBriefEntryView(CamelModel):
    case_id: str
    ticker: str | None
    headline: str
    change_summary: str
    why_it_matters: str
    thesis_impact: str
    changes: list[ChangeFindingView]

    @classmethod
    def from_domain(cls, entry: DailyBriefEntry) -> "DailyBriefEntryView":
        return cls(
            case_id=entry.case_id,
            ticker=entry.ticker,
            headline=entry.headline,
            change_summary=entry.change_summary,
            why_it_matters=entry.why_it_matters,
            thesis_impact=entry.thesis_impact.value,
            changes=[ChangeFindingView.from_domain(c) for c in entry.changes],
        )


class DailyBriefView(CamelModel):
    generated_at: datetime
    summary: str
    entries: list[DailyBriefEntryView]

    @classmethod
    def from_domain(cls, brief: DailyBrief) -> "DailyBriefView":
        return cls(
            generated_at=brief.generated_at,
            summary=brief.summary,
            entries=[DailyBriefEntryView.from_domain(e) for e in brief.entries],
        )
