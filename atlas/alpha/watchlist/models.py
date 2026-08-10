"""Data model for Atlas Alpha's provisional Watchlist state.

See `atlas/alpha/watchlist/__init__.py` for this module's explicit
architectural boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AlphaWatchlistEntry:
    """One ticker on the Watchlist, and the Investment Case it is
    linked to.

    `case_id` is set exactly once, at the moment this entry is first
    added (`AlphaWatchlistService.add_ticker`) -- either a brand-new
    Case, or a Case already linked to this same ticker in Portfolio.
    It is never `None` on a persisted entry: unlike
    `AlphaHolding.case_id` (which may exist case-less between being
    imported and being opened), a Watchlist entry has no comparable
    intermediate state -- Case linkage happens synchronously as part of
    `add_ticker` itself, so there is nothing this field would ever be
    optional for.
    """

    ticker: str
    case_id: str
    added_at: datetime

    def __post_init__(self) -> None:
        if not self.ticker or not self.ticker.strip():
            raise ValueError("AlphaWatchlistEntry.ticker must not be blank")
        if not self.case_id or not self.case_id.strip():
            raise ValueError("AlphaWatchlistEntry.case_id must not be blank")
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
