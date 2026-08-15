"""SQL schema for the Security Confirmation store.

Own `MetaData`, no SQL ForeignKey -- `decision_id` is a plain indexed
string column, matching every other Alpha persistence table's
convention for referencing a Core aggregate id (see
`atlas.core.infrastructure.persistence.outcome.table`,
`atlas.alpha.investment_case_change.table`).

Deliberately **no unique constraint on `decision_id`** -- the v1
single-active-confirmation invariant is enforced at the service layer
(`service.py`), not the schema, precisely so a future append-only
correction/supersession model (Sprint 20 Phase 36/37, not built here)
remains possible without a migration that would have to lift a
constraint this table never had in the first place.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

security_confirmations_table = Table(
    "security_confirmations",
    metadata,
    Column("id", String, primary_key=True),
    Column("decision_id", String, nullable=False, index=True),
    Column("confirmed_ticker", String, nullable=False),
    Column("confirmed_display_name", String, nullable=False),
    Column("confirmed_cik", Integer, nullable=True),
    Column("discovery_method", String, nullable=False),
    Column("discovery_source", String, nullable=False),
    Column("confirmed_at", String, nullable=False),
)


def create_security_confirmation_table(engine: Engine) -> None:
    sync_table_schema(engine, security_confirmations_table)
