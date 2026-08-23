"""SQL schema for the Decision Path read-model cache. One row per
`case_id`, upserted -- mirrors `atlas.alpha.recommendation_conviction
.table.recommendation_conviction_result_table` exactly. The path is
always computed live -- this table exists only so the *previous*
computation can be read back for `detect_decision_path_change`'s own
change detection.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decision_path_result_table = Table(
    "decision_path_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_decision_path_result_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_path_result_table)
