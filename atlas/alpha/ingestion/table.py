"""SQL schema for the Ingestion read-model cache (Deliverable 6/8/9/10's
own read models). One row per `case_id`, upserted (delete-then-insert),
the same "latest state only" persistence `atlas.alpha.monitoring
.table.monitoring_result_table` already establishes -- this table
exists so a Case's latest `IngestionResult` can be read without
re-running a refresh, never to detect change itself (that stays fully
derived from `atlas.analysis_engine.business_data.versioning`'s own
real `content_hash`/`version_number` machinery each time a refresh
actually runs).
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

ingestion_result_table = Table(
    "ingestion_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=False),
    Column("ran_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_ingestion_result_table(engine: Engine) -> None:
    sync_table_schema(engine, ingestion_result_table)
