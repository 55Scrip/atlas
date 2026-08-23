"""SQL schema for the Decision Readiness read-model cache. One row per
`case_id`, upserted -- mirrors `atlas.alpha.ingestion.table
.ingestion_result_table` exactly. **Not a comparison store either**:
readiness itself is always computed live (`DecisionReadinessService
.assess_for_case`, the same "cheap enough to recompute" choice
`atlas.alpha.evidence_graph` already makes) -- this table exists only
so the *previous* computation's own status can be read back for
Deliverable 10/11's change detection (`engine.detect_readiness_change`),
never to decide the current status itself.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decision_readiness_result_table = Table(
    "decision_readiness_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_decision_readiness_result_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_readiness_result_table)
