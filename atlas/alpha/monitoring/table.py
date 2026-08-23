"""SQL schema for the Monitoring read-model cache (Deliverable 21).

**Not a comparison store.** Unlike `evidence_snapshot_table`/
`investment_case_snapshot_table`, this table is not what Monitoring
compares against to detect change -- every comparison Monitoring
performs is already handled by Evidence Timeline's and Change
Intelligence's own snapshot repositories (see `service.py`'s own module
docstring). This table exists only so `GET /monitoring/results` can
serve the last run's output without recomputing it: one row per
`case_id`, always overwritten on the next run, never accumulated into a
history of its own.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

monitoring_result_table = Table(
    "monitoring_results",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("ticker", String, nullable=True),
    Column("generated_at", String, nullable=False),
    Column("result_json", String, nullable=False),
)


def create_monitoring_result_table(engine: Engine) -> None:
    sync_table_schema(engine, monitoring_result_table)


# ---------------------------------------------------------------------
# Atlas Intelligence Sprint 8 -- Automated Monitoring Operations.
# One row per `MonitoringService.run()` call -- genuinely append-only
# (unlike `monitoring_result_table` above), since a run's own history
# is exactly what Deliverable 7's `RUNNING`/`FAILED` status and
# Deliverable 14's "last monitoring run" read model need to answer
# honestly. Written at start (`status="running"`, `completed_at=NULL`)
# and updated once at completion -- never a second row per run.
# ---------------------------------------------------------------------

monitoring_run_record_table = Table(
    "monitoring_run_records",
    metadata,
    Column("run_id", String, primary_key=True),
    Column("status", String, nullable=False),
    Column("started_at", String, nullable=False),
    Column("completed_at", String, nullable=True),
    Column("forced", String, nullable=False),
    Column("evaluated_count", String, nullable=False),
    Column("skipped_count", String, nullable=False),
    Column("failures_json", String, nullable=False),
)


def create_monitoring_run_record_table(engine: Engine) -> None:
    sync_table_schema(engine, monitoring_run_record_table)
