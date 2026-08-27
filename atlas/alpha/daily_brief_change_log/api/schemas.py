"""HTTP request/response schema for the Daily Brief Change Log API.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
matching every other Alpha schema module. The wire shape is already
grouped one-per-ticker (`synthesis.py::group_by_ticker`) -- the
frontend never re-derives "one company, one message" itself.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.daily_brief_change_log.synthesis import TickerChangeGroup
from atlas.core.infrastructure.api.serialization import CamelModel


class ChangeLogEntryView(CamelModel):
    id: str
    ticker: str
    case_id: str | None
    reason_code: str
    value: str | None
    secondary_value: str | None
    label: str | None
    headline: str
    detected_at: datetime
    seen_at: datetime | None


class TickerChangeGroupView(CamelModel):
    ticker: str
    primary: ChangeLogEntryView
    additional_count: int
    is_new: bool

    @staticmethod
    def from_domain(group: TickerChangeGroup) -> "TickerChangeGroupView":
        primary = group.primary
        return TickerChangeGroupView(
            ticker=group.ticker,
            primary=ChangeLogEntryView(
                id=primary.id,
                ticker=primary.ticker,
                case_id=primary.case_id,
                reason_code=primary.reason_code,
                value=primary.value,
                secondary_value=primary.secondary_value,
                label=primary.label,
                headline=primary.headline,
                detected_at=primary.detected_at,
                seen_at=primary.seen_at,
            ),
            additional_count=group.additional_count,
            is_new=group.is_new,
        )


class MarkSeenRequest(CamelModel):
    change_ids: list[str]
