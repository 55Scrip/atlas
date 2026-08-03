"""SQL schema for the Evidence store.

Own MetaData, no foreign keys — Evidence introduces no relationship to
Decision, DecisionContext, or Hypothesis. Table name is singular
(`evidence`), matching "evidence"'s treatment as an uncountable noun in
this domain and API naming.

Atlas Alpha, Evidence Sprint 1: `observation_id` is a plain indexed
string column, matching Interpretation's own established convention for
the identical relationship — no SQL ForeignKey (existence is checked by
the application service, not a database constraint).
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
    Column("observation_id", String, nullable=False, index=True),
    Column("statement", String, nullable=False),
    Column("direction", String, nullable=False),
    Column("source", String, nullable=True),
    Column("note", String, nullable=True),
    Column("observed_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_evidence_table(engine: Engine) -> None:
    sync_table_schema(engine, evidence_table)
