"""SQL schema for the Recommendation Conviction read-model cache. One
row per `case_id`, upserted -- mirrors `atlas.alpha.investment_decision
.table.investment_decision_result_table` exactly. Conviction is always
computed live -- this table exists only so the *previous* computation
can be read back for `detect_conviction_change`'s own change detection.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

recommendation_conviction_result_table = Table(
    "recommendation_conviction_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_recommendation_conviction_result_table(engine: Engine) -> None:
    sync_table_schema(engine, recommendation_conviction_result_table)
