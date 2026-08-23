"""SQL schema for the Decision Memory snapshot store. Mirrors
`atlas.alpha.investment_case_change.table.investment_case_snapshot_table`'s
own shape exactly -- the same append-only, idempotent-by-`content_hash`
discipline already established in this codebase, not a novel one
invented here.

`id` is a synthetic, deterministic `f"{case_id}:{recorded_at}"`.
`change_json` is `NULL` only for a Case's first-ever row (a baseline
has nothing to persist -- `get_history` derives it structurally); every
later row's own `DecisionMemoryChange` is persisted once, here, at the exact
moment it was detected, immune to any later change in `detect_decision
_change`'s own rules.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decision_memory_snapshot_table = Table(
    "decision_memory_snapshots",
    metadata,
    Column("id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("ticker", String, nullable=True),
    Column("recorded_at", String, nullable=False),
    Column("content_hash", String, nullable=False),
    Column("snapshot_json", String, nullable=False),
    Column("change_json", String, nullable=True),
)


def create_decision_memory_snapshot_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_memory_snapshot_table)
