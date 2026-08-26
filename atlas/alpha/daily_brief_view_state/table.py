"""SQL schema for Since You Were Here's one piece of new state.

One row per `user_id` (the table's own primary key) -- mirrors
`alpha_watchlist_entry_table`'s own "normalized table, one row per real
identity" shape, not Portfolio's single-row JSON-blob singleton, since
a second real user would need a second row, not a second column.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

daily_brief_view_state_table = Table(
    "daily_brief_view_state",
    metadata,
    Column("user_id", String, primary_key=True),
    # ISO-8601 string, the same convention every other timestamp column
    # in this codebase already uses (e.g. `alpha_watchlist_entry.added_at`).
    # NULL means "never viewed" -- a real, honest absence, not a
    # fabricated epoch.
    Column("last_viewed_at", String, nullable=True),
)


def create_daily_brief_view_state_table(engine: Engine) -> None:
    sync_table_schema(engine, daily_brief_view_state_table)
