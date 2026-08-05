"""SQL schema for Atlas Alpha's provisional external-trade log.

Records confirmed external trade executions, each referencing an
existing, immutable Core Outcome by id (`outcome_id`, the primary key --
at most one trade log entry per Outcome). This table is Alpha-only and
provisional (see `atlas/alpha/portfolio/__init__.py`); it never causes
Outcome to be written to or modified, and Outcome never references it
back (Alpha Sprint 1B: "Outcome must never reference Alpha").
"""
from __future__ import annotations

from sqlalchemy import Column, Float, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

alpha_trade_log_table = Table(
    "alpha_trade_log",
    metadata,
    Column("outcome_id", String, primary_key=True),
    Column("decision_id", String, nullable=False, index=True),
    Column("security", String, nullable=False, index=True),
    Column("transaction_type", String, nullable=False),
    Column("quantity", Float, nullable=False),
    Column("execution_price", Float, nullable=False),
    Column("fees", Float, nullable=True),
    Column("executed_at", String, nullable=False),
)


def create_alpha_trade_log_table(engine: Engine) -> None:
    sync_table_schema(engine, alpha_trade_log_table)
