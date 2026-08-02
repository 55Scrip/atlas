"""SQL schema for the Decision Store.

This bounded context owns its own MetaData rather than registering on the
legacy `atlas.database.connection.Base` used by the company/financials
tables — Decision Capture's schema lifecycle should not be coupled to an
unrelated domain's.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decisions_table = Table(
    "decisions",
    metadata,
    Column("id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("user_id", String, nullable=False, index=True),
    Column("decision_type", String, nullable=False),
    Column("subject", String, nullable=False),
    Column("reason", String, nullable=False),
    Column("confidence", Integer, nullable=False),
    Column("decided_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
    Column("source", String, nullable=False),
)


def create_decision_table(engine: Engine) -> None:
    sync_table_schema(engine, decisions_table)
