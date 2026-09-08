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


class WatchlistEntrySummaryView(CamelModel):
    """One Watchlist prospect, composed for a list surface.

    Every field is projected from already-persisted Atlas state. This
    view exists because Watchlist previously read company identity from
    `GET /cases/{case_id}/analysis` -- once per entry -- and that
    endpoint depends on the Alpha Vantage price provider, the quota
    tracker and the price refresh coordinator, writes an evidence
    snapshot on every call, and may schedule a background price
    refresh. Its own code says that lazy refresh is meant for "a
    single-ticker view like this one (never Portfolio/Watchlist's own
    list endpoints)"; calling it per row defeated exactly that
    intention. Twenty prospects meant twenty provider-touching calls
    and twenty snapshot writes just to draw a list.

    Canonical enum *values* only -- never rendered text. Investor-facing
    wording stays the frontend's job, so one canonical state keeps one
    label across every surface that shows it.

    `company_name`/`sector` are `None` when no `COMPANY_PROFILE` record
    has been ingested -- the honest absence `extract_company_profile`
    already expresses, never a guessed name.
    """

    ticker: str
    case_id: str
    added_at: datetime
    company_name: str | None
    sector: str | None
    decision_support_level: str
    analysis_coverage_level: str
