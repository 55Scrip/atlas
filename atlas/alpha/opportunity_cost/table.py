"""SQL schema for the Opportunity Cost read-model cache. One row per
`case_id`, upserted -- mirrors `atlas.alpha.decision_path.table
.decision_path_result_table` exactly. Always computed live -- this
table exists only so the *previous* computation can be read back for
`detect_opportunity_cost_change`'s own change detection.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

opportunity_cost_result_table = Table(
    "opportunity_cost_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_opportunity_cost_result_table(engine: Engine) -> None:
    sync_table_schema(engine, opportunity_cost_result_table)
