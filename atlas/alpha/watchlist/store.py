"""Persistence for Atlas Alpha's provisional Watchlist state.

`add` is the only write and is always an INSERT -- a Watchlist entry's
`case_id` is set exactly once, at creation, and never changes afterward
(see `models.AlphaWatchlistEntry`'s own docstring), so there is nothing
to update, mirroring `business_record_table`'s own repository shape.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.table import alpha_watchlist_entry_table


class AlphaWatchlistStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, entry: AlphaWatchlistEntry) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(alpha_watchlist_entry_table).values(**_to_row(entry)))

    def list_all(self) -> tuple[AlphaWatchlistEntry, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(alpha_watchlist_entry_table)).mappings().all()
        return tuple(_to_entry(row) for row in rows)

    def get_by_ticker(self, ticker: str) -> AlphaWatchlistEntry | None:
        normalized = ticker.strip().upper()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(alpha_watchlist_entry_table).where(
                        alpha_watchlist_entry_table.c.ticker == normalized
                    )
                )
                .mappings()
                .first()
            )
        return _to_entry(row) if row is not None else None

    def get_by_case_id(self, case_id: str) -> AlphaWatchlistEntry | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(alpha_watchlist_entry_table).where(
                        alpha_watchlist_entry_table.c.case_id == case_id
                    )
                )
                .mappings()
                .first()
            )
        return _to_entry(row) if row is not None else None


def _to_row(entry: AlphaWatchlistEntry) -> dict[str, Any]:
    return {
        "ticker": entry.ticker,
        "case_id": entry.case_id,
        "added_at": entry.added_at.isoformat(),
    }


def _to_entry(row: Mapping[str, Any]) -> AlphaWatchlistEntry:
    return AlphaWatchlistEntry(
        ticker=row["ticker"],
        case_id=row["case_id"],
        added_at=datetime.fromisoformat(row["added_at"]),
    )
