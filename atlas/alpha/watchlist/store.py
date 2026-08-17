"""Persistence for Atlas Alpha's provisional Watchlist state.

Ticker -> Existing Case Resolution Sprint: `remove` became a soft
delete (`removed_at` set, row kept) instead of a DELETE, so a ticker's
own `case_id` history survives being removed from the Watchlist --
see `table.py`'s own comment on `removed_at` for why. `add` became an
upsert keyed by `ticker` (the table's own primary key) rather than a
plain INSERT, since the row for a previously-removed ticker already
exists and must be reactivated (case_id preserved, `removed_at`
cleared) rather than re-inserted. The table still has no foreign-key
relationship to Case/Decision/Evidence/Company data, so none of this
can cascade into any of it.

`list_all` and `get_by_ticker` are "currently on the Watchlist" reads
-- both filter to `removed_at IS NULL`, preserving every pre-existing
caller's behavior exactly (a removed ticker must not reappear in the
Watchlist listing or look "present" to `add_ticker`'s own idempotency
check). `get_by_ticker_including_removed` and `get_by_case_id` are
deliberately NOT filtered -- see their own docstrings.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine

from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.table import alpha_watchlist_entry_table


class AlphaWatchlistStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, entry: AlphaWatchlistEntry) -> None:
        """Insert a brand-new row, or reactivate (and overwrite the
        case_id/added_at of) an existing one for the same ticker --
        an upsert, not a plain INSERT, because a previously-removed
        ticker's row still physically exists (soft-deleted) and would
        otherwise violate the `ticker` primary key on re-add."""
        normalized = entry.ticker.strip().upper()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(alpha_watchlist_entry_table.c.ticker).where(
                    alpha_watchlist_entry_table.c.ticker == normalized
                )
            ).first()
            if existing is None:
                connection.execute(insert(alpha_watchlist_entry_table).values(**_to_row(entry)))
            else:
                connection.execute(
                    update(alpha_watchlist_entry_table)
                    .where(alpha_watchlist_entry_table.c.ticker == normalized)
                    .values(case_id=entry.case_id, added_at=entry.added_at.isoformat(), removed_at=None)
                )

    def remove(self, ticker: str, removed_at: datetime) -> None:
        normalized = ticker.strip().upper()
        with self._engine.begin() as connection:
            connection.execute(
                update(alpha_watchlist_entry_table)
                .where(alpha_watchlist_entry_table.c.ticker == normalized)
                .values(removed_at=removed_at.isoformat())
            )

    def list_all(self) -> tuple[AlphaWatchlistEntry, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(alpha_watchlist_entry_table).where(
                        alpha_watchlist_entry_table.c.removed_at.is_(None)
                    )
                )
                .mappings()
                .all()
            )
        return tuple(_to_entry(row) for row in rows)

    def get_by_ticker(self, ticker: str) -> AlphaWatchlistEntry | None:
        """Currently-on-the-Watchlist lookup only -- see
        `get_by_ticker_including_removed` for the ticker's full
        history, including a since-removed entry."""
        normalized = ticker.strip().upper()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(alpha_watchlist_entry_table).where(
                        alpha_watchlist_entry_table.c.ticker == normalized,
                        alpha_watchlist_entry_table.c.removed_at.is_(None),
                    )
                )
                .mappings()
                .first()
            )
        return _to_entry(row) if row is not None else None

    def get_by_ticker_including_removed(self, ticker: str) -> AlphaWatchlistEntry | None:
        """The ticker's own most recent Watchlist entry, active or
        removed -- the persisted signal `case_membership.
        resolve_case_id_for_ticker` reuses to restore continuity with
        a ticker's historical Case after it was removed and is being
        re-added, without ever guessing or fabricating a new one."""
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

    def list_all_including_removed(self) -> tuple[AlphaWatchlistEntry, ...]:
        """Every entry this ticker has ever had on the Watchlist,
        active or removed -- the bulk counterpart to
        `get_by_ticker_including_removed`, used where a caller needs
        to check many tickers at once (`AlphaPortfolioService
        ._known_watchlist_case_ids`'s own cross-context Case reuse for
        Portfolio import) rather than one at a time."""
        with self._engine.connect() as connection:
            rows = connection.execute(select(alpha_watchlist_entry_table)).mappings().all()
        return tuple(_to_entry(row) for row in rows)

    def get_by_case_id(self, case_id: str) -> AlphaWatchlistEntry | None:
        """Deliberately not filtered to active-only: this is what lets
        `InvestmentCaseCompositionService._assemble` keep recovering a
        Watchlist-only Case's ticker (for BusinessRecord/company-
        profile display) after the Watchlist entry has been removed --
        the Case itself was never deleted, so its display should not
        depend on current membership either. Two different tickers are
        not expected to ever share a `case_id` in this table -- see
        `case_membership.resolve_case_id_for_ticker`, the only path
        that assigns a `case_id` to a ticker, which only ever reuses a
        `case_id` already tied to that exact ticker -- but `.first()`
        is used defensively rather than assuming a DB-level uniqueness
        constraint that does not exist on this column."""
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
        "removed_at": None,
    }


def _to_entry(row: Mapping[str, Any]) -> AlphaWatchlistEntry:
    return AlphaWatchlistEntry(
        ticker=row["ticker"],
        case_id=row["case_id"],
        added_at=datetime.fromisoformat(row["added_at"]),
    )
