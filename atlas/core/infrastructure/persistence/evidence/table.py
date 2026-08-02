"""SQL schema for the Evidence store.

Own MetaData, no foreign keys — Evidence introduces no relationship to
Decision, DecisionContext, Observation, Hypothesis, or any other
aggregate. Table name is singular (`evidence`), matching "evidence"'s
treatment as an uncountable noun in this domain and API naming.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

evidence_table = Table(
    "evidence",
    metadata,
    Column("evidence_id", String, primary_key=True),
    Column("statement", String, nullable=False),
    Column("direction", String, nullable=False),
    Column("source", String, nullable=True),
    Column("note", String, nullable=True),
    Column("observed_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_evidence_table(engine: Engine) -> None:
    sync_table_schema(engine, evidence_table)
