"""SQL schema for Daily Brief 2.0's one piece of new durable state.

One row per (user_id, ticker, reason_code, value, secondary_value)
tuple ever observed -- normalized, not a JSON blob, since the read
path (`store.py::list_recent`) needs to filter/order/group by these
columns, not just replay an opaque history. `id` is still the real
primary key (server-generated) so a later row with the same natural
key but a different `label`/`headline` -- the same transition observed
again with a freshly-worded sentence -- can be recognized as a dup by
`record_if_new`'s own lookup without needing the natural key itself to
be the primary key.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

daily_brief_change_log_table = Table(
    "daily_brief_change_log",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("ticker", String, nullable=False),
    Column("case_id", String, nullable=True),
    Column("reason_code", String, nullable=False),
    Column("value", String, nullable=True),
    Column("secondary_value", String, nullable=True),
    Column("label", String, nullable=True),
    Column("headline", String, nullable=False),
    # ISO-8601 strings, the same convention `daily_brief_view_state`
    # already uses for its own `last_viewed_at`.
    Column("detected_at", String, nullable=False),
    # NULL means NEW (Phase 8) -- an honest absence, never a
    # fabricated past timestamp standing in for "not yet seen."
    Column("seen_at", String, nullable=True),
    # Real, already-computed data used for ordering/materiality at
    # read time -- never re-derived from `value` string-matching.
    Column("priority_rank", Integer, nullable=False),
)


def create_daily_brief_change_log_table(engine: Engine) -> None:
    sync_table_schema(engine, daily_brief_change_log_table)
