"""SQL schema for the Alpha Vantage daily call-budget counter
(Internal Alpha Stabilization 1, MSFT price root cause fix).

One row per UTC calendar date -- `call_date` alone is primary key, so
"today's count" is always exactly one row lookup, and a new date
simply has no row yet (count 0) rather than needing an explicit daily
reset job. Persisted (not in-memory) specifically so it survives the
frequent local dev-server restarts this project already has -- an
in-memory counter would silently let the app exceed the real,
external 25-calls/day Alpha Vantage limit every time the process
restarts.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

alpha_vantage_daily_call_count_table = Table(
    "alpha_vantage_daily_call_count",
    metadata,
    Column("call_date", String, primary_key=True),
    Column("call_count", Integer, nullable=False),
)


def create_alpha_vantage_daily_call_count_table(engine: Engine) -> None:
    sync_table_schema(engine, alpha_vantage_daily_call_count_table)
