"""Persisted daily call-budget tracker for Alpha Vantage (Internal
Alpha Stabilization 1, MSFT price root cause fix).

Confirmed against the real, currently configured key (live probe,
2026-08-24): the free tier's own "Information" response states the
limit explicitly -- **25 requests per day**, plus a ~1-request/second
burst cap the provider's own `_pace()` already enforces separately.
This tracker exists because Alpha Vantage's response carries no
"requests remaining" field of its own -- Atlas has to count its own
calls to know when it is close to that ceiling, rather than finding
out by receiving a real rate-limit response.

Counts **every** real Alpha Vantage call, not just price refreshes --
wired via `AlphaVantageMarketDataProvider`'s `on_request` hook (see
that class's own docstring), so a full company enrichment's
`GLOBAL_QUOTE` + `OVERVIEW` (or more) calls count exactly as much
against the same real, shared, external limit as a price-only refresh
does. A tracker that only counted price refreshes would be
systematically wrong about how much real budget is actually left.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.quota_table import (
    alpha_vantage_daily_call_count_table,
    create_alpha_vantage_daily_call_count_table,
)

__all__ = ["AlphaVantageQuotaTracker", "ALPHA_VANTAGE_FREE_TIER_DAILY_LIMIT"]

#: Confirmed live against the real configured key (see this module's
#: own docstring) -- not an assumption.
ALPHA_VANTAGE_FREE_TIER_DAILY_LIMIT = 25


def _today(clock: datetime | None = None) -> str:
    return (clock or datetime.now(timezone.utc)).date().isoformat()


class AlphaVantageQuotaTracker:
    """One instance per request is fine and expected (cheap, no
    in-memory state of its own) -- every real number lives in the
    `alpha_vantage_daily_call_count` table, keyed by UTC date, so two
    instances (or two process restarts) never disagree."""

    def __init__(self, engine: Engine, *, daily_limit: int = ALPHA_VANTAGE_FREE_TIER_DAILY_LIMIT) -> None:
        create_alpha_vantage_daily_call_count_table(engine)
        self._engine = engine
        self._daily_limit = daily_limit

    def calls_used_today(self) -> int:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(alpha_vantage_daily_call_count_table.c.call_count).where(
                    alpha_vantage_daily_call_count_table.c.call_date == _today()
                )
            ).first()
        return row[0] if row is not None else 0

    def remaining_today(self) -> int:
        return max(0, self._daily_limit - self.calls_used_today())

    def has_budget(self) -> bool:
        return self.remaining_today() > 0

    def record_call(self) -> None:
        """Atomic increment-or-insert for today's row -- safe against
        the same low-concurrency-but-still-real race a background
        refresh and a manual "Uppdatera" click could otherwise hit."""
        today = _today()
        statement = sqlite_insert(alpha_vantage_daily_call_count_table).values(call_date=today, call_count=1)
        statement = statement.on_conflict_do_update(
            index_elements=[alpha_vantage_daily_call_count_table.c.call_date],
            set_={"call_count": alpha_vantage_daily_call_count_table.c.call_count + 1},
        )
        with self._engine.begin() as connection:
            connection.execute(statement)
