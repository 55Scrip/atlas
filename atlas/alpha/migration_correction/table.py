"""SQL schema for the migration-artifact correction ledger.

One row per correction write, never updated, never deleted: which stored
row was retracted or had its persisted transition recomputed, why, under
which methodology and migration window, what it held before, what it holds
after, and which checks the correction passed first. The corrected rows
themselves are never deleted -- a retracted row keeps every column it had
and points back here through its own `retracted_by`.

`id` is deterministic, `f"{correction_id}/{target_table}/{target_row_id}"`,
so re-running the same correction finds its own entries and writes nothing.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

migration_artifact_correction_table = Table(
    "migration_artifact_corrections",
    metadata,
    Column("id", String, primary_key=True),
    Column("correction_id", String, nullable=False, index=True),
    # `retract` or `recompute_transition`.
    Column("action", String, nullable=False),
    Column("target_table", String, nullable=False),
    Column("target_row_id", String, nullable=False, index=True),
    Column("case_id", String, nullable=False),
    Column("reason", String, nullable=False),
    Column("window_start", String, nullable=False),
    Column("window_end", String, nullable=False),
    # The analysis methodology the corrected rows were produced under,
    # and that the recomputation ran with.
    Column("methodology", String, nullable=False),
    # For `recompute_transition`: the surviving row the transition is now
    # diffed against. NULL for `retract`.
    Column("predecessor_row_id", String, nullable=True),
    Column("before_json", String, nullable=False),
    Column("after_json", String, nullable=False),
    Column("verification_json", String, nullable=False),
    Column("applied_at", String, nullable=False),
)


def create_migration_artifact_correction_table(engine: Engine) -> None:
    sync_table_schema(engine, migration_artifact_correction_table)
