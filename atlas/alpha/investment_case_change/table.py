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

`change_intelligence_json` (History v1): the `ChangeIntelligence`
already computed for this row's own transition *against its immediate
predecessor* at the moment this row was written -- persisted once, here,
rather than deterministically recomputed later, so History v1 (and any
future reader) sees the exact historical interpretation Atlas reached at
the time, immune to a later change in `compare_snapshots`'s own rules
(see `atlas.alpha.investment_case_history`'s own module docstring for
the full "persisted vs. recomputed" reasoning). `NULL` for: (a) a Case's
first-ever row (a baseline is never a change, nothing to persist), and
(b) any row written before this column existed -- `sync_table_schema`
adds it as a nullable `ALTER TABLE`, so older rows keep their exact prior
meaning, read back as "no change transition recorded for this entry"
rather than a fabricated one (see `repository.py`'s own defensive
deserialization).
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
    Column("change_intelligence_json", String, nullable=True),
)


def create_investment_case_snapshot_table(engine: Engine) -> None:
    sync_table_schema(engine, investment_case_snapshot_table)
