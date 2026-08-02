"""SQL schema for the Hypothesis store.

Own MetaData, no foreign keys — Hypothesis introduces no relationship to
Decision, DecisionContext, Observation, or any other aggregate.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

hypotheses_table = Table(
    "hypotheses",
    metadata,
    Column("hypothesis_id", String, primary_key=True),
    Column("statement", String, nullable=False),
    Column("note", String, nullable=True),
    Column("formulated_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_hypothesis_table(engine: Engine) -> None:
    sync_table_schema(engine, hypotheses_table)
