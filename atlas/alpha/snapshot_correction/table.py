"""Ledger for snapshot corrections that are not migration artifacts.

`migration_artifact_corrections` already records one kind of correction, and
records it well -- but it says *migration artifact* in its name and requires a
methodology and a migration window in every row. A snapshot duplicated by two
processes racing is none of those things: no methodology produced it, no
migration window contains it, and filing it there would make the record claim
something that did not happen. So this is a second, smaller ledger for
corrections whose reason is something else, with `kind` naming what that was.

Same discipline as the other one: one row per correction write, never updated,
never deleted. The corrected row keeps every column it had and points back
here through its own `retracted_by`. `id` is deterministic --
`f"{correction_id}/{target_table}/{target_row_id}"` -- so re-running a
correction finds its own entry and writes nothing.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

snapshot_correction_table = Table(
    "snapshot_corrections",
    metadata,
    Column("id", String, primary_key=True),
    Column("correction_id", String, nullable=False, index=True),
    #: What actually went wrong. `concurrency_duplicate` is the first.
    Column("kind", String, nullable=False),
    Column("action", String, nullable=False),
    Column("target_table", String, nullable=False),
    Column("target_row_id", String, nullable=False, index=True),
    #: The row that survives and continues to represent this observation --
    #: without it a reader can see that something was hidden but not what it
    #: was a duplicate *of*.
    Column("canonical_row_id", String, nullable=True),
    Column("case_id", String, nullable=False),
    Column("reason", String, nullable=False),
    #: Every guard that had to pass, with the values it compared, so the
    #: correction can be re-argued later without re-deriving it from scratch.
    Column("verification_json", String, nullable=False),
    Column("before_json", String, nullable=False),
    Column("after_json", String, nullable=False),
    Column("applied_at", String, nullable=False),
)

RETRACT = "retract"
CONCURRENCY_DUPLICATE = "concurrency_duplicate"


def create_snapshot_correction_table(engine: Engine) -> None:
    sync_table_schema(engine, snapshot_correction_table)
