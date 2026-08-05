"""SQL schema for Atlas Alpha's provisional portfolio state.

Single-row table (Sprint 1A: at most one state exists, per the singleton
design in `models.AlphaPortfolioState`). Holdings are stored as a
JSON-serialized column rather than a normalized child table — this is a
provisional module (see `atlas/alpha/portfolio/__init__.py`); a
normalized schema is deferred to whatever architecture eventually
resolves `APS-006` §24, not invented speculatively here.

Reuses `sync_table_schema` from `atlas.core.infrastructure.persistence`
— a shared, generic utility, not a Core domain construct — for the same
create-or-safely-add-nullable-columns behavior every other table module
in this codebase already relies on.
"""
from __future__ import annotations

from sqlalchemy import Column, Float, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

alpha_portfolio_state_table = Table(
    "alpha_portfolio_state",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("established_at", String, nullable=False),
    Column("updated_at", String, nullable=False),
    Column("entry_mode", String, nullable=False),
    Column("holdings_json", String, nullable=False),
    Column("cash_weight_percent", Float, nullable=True),
    Column("cash_value_absolute", Float, nullable=True),
    Column("objective", String, nullable=True),
    Column("horizon", String, nullable=True),
    Column("preferences_notes", String, nullable=True),
)


def create_alpha_portfolio_state_table(engine: Engine) -> None:
    sync_table_schema(engine, alpha_portfolio_state_table)
