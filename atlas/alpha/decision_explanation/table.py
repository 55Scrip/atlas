"""SQL schema for the Decision Explanation read-model cache. One row
per `case_id`, upserted -- mirrors `atlas.alpha.opportunity_cost.table
.opportunity_cost_result_table` exactly. Always computed live -- this
table exists only so the *previous* computation can be read back for
`detect_decision_explanation_change`'s own change detection. This is
deliberately a live cache, not a second historical ledger:
`atlas.alpha.decision_memory` already owns durable, append-only
decision history (Sprint 5) -- duplicating that responsibility here
would be exactly the "redesign an earlier layer" the brief forbids.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decision_explanation_result_table = Table(
    "decision_explanation_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_decision_explanation_result_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_explanation_result_table)
