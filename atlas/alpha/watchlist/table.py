"""SQL schema for Atlas Alpha's provisional Watchlist state.

One row per ticker (`ticker` is the primary key) -- unlike Portfolio's
single-row JSON-blob singleton (`atlas/alpha/portfolio/table.py`),
Watchlist entries have no shared singleton fields (no cash, no entry
mode, no preferences) to bundle them under, so a normalized table is
the natural, honest shape here, mirroring how `business_record_table`
(`atlas/alpha/business_data_refresh/table.py`) already stores one row
per record rather than a blob.

Reuses `sync_table_schema`, the same shared, generic create-or-safely-
add-nullable-columns utility every other table module in this codebase
already relies on.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

alpha_watchlist_entry_table = Table(
    "alpha_watchlist_entry",
    metadata,
    Column("ticker", String, primary_key=True),
    Column("case_id", String, nullable=False),
    Column("added_at", String, nullable=False),
    # Ticker -> Existing Case Resolution Sprint: `removed_at` (nullable,
    # added via `sync_table_schema`'s safe-add path) turns Remove into a
    # soft delete -- NULL means "currently on the Watchlist," a
    # timestamp means "removed, but its ticker->case_id linkage is kept"
    # -- the same append-only, never-delete-history convention this
    # codebase already established for `SecurityConfirmationEvent`
    # (`"revoked"` events are never deleted either). The row's own
    # `ticker` primary key stays the one and only identity; no new
    # concept is introduced.
    Column("removed_at", String, nullable=True),
)


def create_alpha_watchlist_entry_table(engine: Engine) -> None:
    sync_table_schema(engine, alpha_watchlist_entry_table)
