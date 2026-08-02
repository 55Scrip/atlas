"""SQL schema for the Case store.

Own MetaData, no foreign keys — Case is the foundational ownership
boundary; it depends on no other aggregate (DO-IMP-001 scope control).
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

cases_table = Table(
    "cases",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("recorded_at", String, nullable=False),
)


def create_case_table(engine: Engine) -> None:
    # Concurrency-safe: sync_table_schema serializes per table name
    # (Sprint 1, Commit 11) — no lock of this module's own is needed.
    sync_table_schema(engine, cases_table)
