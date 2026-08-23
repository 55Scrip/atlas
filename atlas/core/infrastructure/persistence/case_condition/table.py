"""SQL schema for the CaseCondition event store (ADR-CC-001).

Own `MetaData`, no `ForeignKey` on `condition_id`/`case_id`/
`decision_id`/`superseded_by_condition_id` — the codebase-wide no-FK
convention (see `decision_draft/table.py`'s own identical choice,
Sprint 9). No uniqueness constraint: many events share one
`condition_id`, and many conditions may share one `case_id` or
`decision_id`.
"""
from __future__ import annotations

from sqlalchemy import Column, Float, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

case_condition_events_table = Table(
    "case_condition_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("condition_id", String, nullable=False, index=True),
    Column("case_id", String, nullable=False, index=True),
    Column("decision_id", String, nullable=True, index=True),
    Column("event_type", String, nullable=False),
    Column("predicate_text", String, nullable=True),
    Column("role", String, nullable=True),
    Column("authorship", String, nullable=True),
    Column("structured_kind", String, nullable=True),
    Column("threshold_date", String, nullable=True),
    Column("threshold_metric", String, nullable=True),
    Column("threshold_operator", String, nullable=True),
    Column("threshold_value", Float, nullable=True),
    Column("observed_value", Float, nullable=True),
    Column("superseded_by_condition_id", String, nullable=True),
    Column("recorded_at", String, nullable=False),
)


def create_case_condition_events_table(engine: Engine) -> None:
    sync_table_schema(engine, case_condition_events_table)
