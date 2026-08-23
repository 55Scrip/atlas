"""SQL schema for the Decision Reliability read-model cache. One row
per `case_id`, upserted -- mirrors `atlas.alpha.decision_explanation
.table.decision_explanation_result_table` exactly. Always computed
live -- this table exists only so the *previous* computation can be
read back for `detect_reliability_change`'s own change detection.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decision_reliability_result_table = Table(
    "decision_reliability_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_decision_reliability_result_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_reliability_result_table)
