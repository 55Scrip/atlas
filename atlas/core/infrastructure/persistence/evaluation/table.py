"""SQL schema for the Evaluation store.

Own MetaData, no SQL ForeignKey — outcome_id is a plain indexed string
column, matching the rest of this codebase's convention.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

evaluations_table = Table(
    "evaluations",
    metadata,
    Column("evaluation_id", String, primary_key=True),
    Column("outcome_id", String, nullable=False, index=True),
    Column("statement", String, nullable=False),
    Column("note", String, nullable=True),
    Column("evaluated_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_evaluation_table(engine: Engine) -> None:
    sync_table_schema(engine, evaluations_table)
