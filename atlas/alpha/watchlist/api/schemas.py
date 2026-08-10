"""HTTP request/response schemas for the Alpha Watchlist API.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
matching every other Alpha schema module.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.core.infrastructure.api.serialization import CamelModel


class AddWatchlistTickerRequestBody(CamelModel):
    ticker: str


class WatchlistEntryView(CamelModel):
    ticker: str
    case_id: str
    added_at: datetime

    @classmethod
    def from_domain(cls, entry: AlphaWatchlistEntry) -> "WatchlistEntryView":
        return cls(ticker=entry.ticker, case_id=entry.case_id, added_at=entry.added_at)
