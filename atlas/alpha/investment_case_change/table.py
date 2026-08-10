"""SQL schema for the Investment Case analytical-snapshot store.

Mirrors `atlas.alpha.business_data_refresh.table.business_record_table`'s
own shape exactly: structural columns for what a caller needs to query
by (`case_id`, ordering by `captured_at`), plus one JSON column for the
comparison-relevant structured content -- the same hybrid "columns for
what's queried, JSON for the rest" pattern that table already
establishes, not a novel one invented here.

`id` is a synthetic, deterministic `f"{case_id}:{captured_at}"` (both
already unique together: this repository only ever inserts a new row
when `content_hash` differs from the current head, and `captured_at`
comes from `CanonicalAnalysis.generated_at`, which is itself unique per
assembly). No `content_hash` unique constraint: two different Cases can
legitimately share an identical structured state.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

investment_case_snapshot_table = Table(
    "investment_case_snapshots",
    metadata,
    Column("id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("captured_at", String, nullable=False),
    Column("content_hash", String, nullable=False),
    Column("current_yield", String, nullable=True),
    Column("snapshot_json", String, nullable=False),
)


def create_investment_case_snapshot_table(engine: Engine) -> None:
    sync_table_schema(engine, investment_case_snapshot_table)
