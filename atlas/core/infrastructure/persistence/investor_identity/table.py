"""SQL schema for InvestorIdentity (ATLAS-009B).

Single-row table by construction: the primary key is always the literal
"singleton". A second INSERT attempt raises IntegrityError at the
database level, enforcing "exactly one Investor Identity per data
store" (ATLAS-009B-D invariant 8) independent of application-code
discipline.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

investor_identity_table = Table(
    "investor_identity",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("established_at", String, nullable=False),
)


def create_investor_identity_table(engine: Engine) -> None:
    sync_table_schema(engine, investor_identity_table)
