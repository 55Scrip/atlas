"""SQL schema for the Investment Decision read-model cache. One row per
`case_id`, upserted -- mirrors `atlas.alpha.decision_readiness.table
.decision_readiness_result_table` exactly. Not a comparison store
either: the decision itself is always computed live -- this table
exists only so the *previous* computation's own action/qualifiers can
be read back for Deliverable 10/11's change detection.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

investment_decision_result_table = Table(
    "investment_decision_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_investment_decision_result_table(engine: Engine) -> None:
    sync_table_schema(engine, investment_decision_result_table)
