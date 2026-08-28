"""SQL schema for learned name-to-ticker resolutions.

Zero-Effort Import Polish (Sprint 11 Phase 1, "previous successful
resolutions"): one row per normalized company name -- a name Atlas
ever resolved (a genuine ambiguity the investor picked one of, or a
name typed manually) is remembered, so it never needs resolving again
on a future import. Deliberately a single, small, single-purpose table
-- no generic "learning" framework, no versioning, no expiry.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

resolved_alias_table = Table(
    "resolved_alias",
    metadata,
    Column("normalized_name", String, primary_key=True),
    Column("ticker", String, nullable=False),
    Column("learned_at", String, nullable=False),
)


def create_resolved_alias_table(engine: Engine) -> None:
    sync_table_schema(engine, resolved_alias_table)
