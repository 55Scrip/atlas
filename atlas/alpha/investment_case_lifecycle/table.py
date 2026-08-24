"""SQL schema for the Investment Case Lifecycle's own regression-
detection history. One row per `case_id`, upserted -- mirrors
`atlas.alpha.decision_readiness.table.decision_readiness_result_table`
exactly. **Not a cache of the lifecycle state itself**: the lifecycle
is always recomputed live from real, current evidence on every read
(the same "cheap enough to recompute" choice every sibling Decision
Layer package already makes) -- this table exists only so the
*previous* evaluation's own Mandatory Core breakdown, state, and
`published_since` can be read back to detect a real regression, never
to decide the current state itself.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

investment_case_lifecycle_history_table = Table(
    "investment_case_lifecycle_history",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_investment_case_lifecycle_history_table(engine: Engine) -> None:
    sync_table_schema(engine, investment_case_lifecycle_history_table)
