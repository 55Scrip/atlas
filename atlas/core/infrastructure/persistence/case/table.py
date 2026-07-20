"""SQL schema for the Case store.

Own MetaData, no foreign keys — Case is the foundational ownership
boundary; it depends on no other aggregate (DO-IMP-001 scope control).
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

cases_table = Table(
    "cases",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("recorded_at", String, nullable=False),
)


def create_case_table(engine: Engine) -> None:
    metadata.create_all(engine, tables=[cases_table])
