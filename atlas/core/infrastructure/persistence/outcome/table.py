"""SQL schema for the Outcome store.

Own MetaData, no SQL ForeignKey — decision_id is a plain indexed string
column, matching the rest of this codebase's convention.
"""

from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

outcomes_table = Table(
    "outcomes",
    metadata,
    Column("outcome_id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("decision_id", String, nullable=False, index=True),
    Column("statement", String, nullable=False),
    Column("note", String, nullable=True),
    Column("occurred_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_outcome_table(engine: Engine) -> None:
    sync_table_schema(engine, outcomes_table)
