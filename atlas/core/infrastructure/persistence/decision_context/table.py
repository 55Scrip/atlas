"""SQL schema for the DecisionContext store.

A separate insert-only table from `decisions`, per API-002's core domain
decision — this bounded context has its own MetaData, same as
decision_context's sibling `decision` persistence module.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

decision_contexts_table = Table(
    "decision_contexts",
    metadata,
    Column("context_id", String, primary_key=True),
    Column("decision_id", String, nullable=False, unique=True, index=True),
    Column("situation", String, nullable=False),
    Column("portfolio_relevance", String, nullable=True),
    Column("capital_considerations", String, nullable=True),
    Column("alternatives_considered", String, nullable=False),
    Column("uncertainties", String, nullable=False),
    Column("captured_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_decision_context_table(engine: Engine) -> None:
    metadata.create_all(engine, tables=[decision_contexts_table])
