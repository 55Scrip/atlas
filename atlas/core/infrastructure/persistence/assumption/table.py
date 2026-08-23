"""SQL schema for the Assumption event store (ADR-AS-001).

Own `MetaData`, no `ForeignKey` on `assumption_id`/`decision_id`/
`case_id`/`superseded_by_assumption_id` — the codebase-wide no-FK
convention (see `decision_draft/table.py`/`case_condition/table.py`'s
own identical choice). `decision_id` is NOT NULL (Decision-anchored,
per ADR-AS-001 §1 — unlike `CaseCondition`'s own optional
`decision_id`); `case_id` is also NOT NULL, but is a denormalized
value derived from the referenced Decision at creation time, never an
independently supplied identity (see `entity.py`'s own docstring).
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

assumption_events_table = Table(
    "assumption_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("assumption_id", String, nullable=False, index=True),
    Column("decision_id", String, nullable=False, index=True),
    Column("case_id", String, nullable=False, index=True),
    Column("event_type", String, nullable=False),
    Column("statement", String, nullable=True),
    Column("authorship", String, nullable=True),
    Column("linked_case_condition_ids", String, nullable=True),
    Column("evidence_id", String, nullable=True),
    Column("note", String, nullable=True),
    Column("severity", String, nullable=True),
    Column("superseded_by_assumption_id", String, nullable=True),
    Column("recorded_at", String, nullable=False),
)


def create_assumption_events_table(engine: Engine) -> None:
    sync_table_schema(engine, assumption_events_table)
