"""SQL schema for the DecisionDraft event store.

Own `MetaData`, no `ForeignKey` on `draft_id`/`case_id`/`user_id`/
`committed_decision_id` — matching the codebase-wide no-FK convention
already established for every other cross-aggregate reference (see
`decision/table.py`'s own docstring). No uniqueness constraint on any
column: many events share one `draft_id`, and many drafts may share one
`case_id` (ADR-DD-001 leaves the cardinality of drafts per Case
unresolved; this design does not impose a cap — see
`DecisionDraft-Implementation-Design.md` §3.4/§5.4).
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

decision_draft_events_table = Table(
    "decision_draft_events",
    metadata,
    Column("id", String, primary_key=True),
    Column("draft_id", String, nullable=False, index=True),
    Column("case_id", String, nullable=False, index=True),
    Column("user_id", String, nullable=False, index=True),
    Column("event_type", String, nullable=False),
    Column("decision_type", String, nullable=True),
    Column("subject", String, nullable=True),
    Column("reason", String, nullable=True),
    Column("confidence", Integer, nullable=True),
    Column("decided_at", String, nullable=True),
    Column("source", String, nullable=True),
    Column("situation", String, nullable=True),
    Column("portfolio_relevance", String, nullable=True),
    Column("capital_considerations", String, nullable=True),
    Column("alternatives_considered", String, nullable=True),
    Column("uncertainties", String, nullable=True),
    Column("committed_decision_id", String, nullable=True, index=True),
    Column("recorded_at", String, nullable=False),
)


def create_decision_draft_events_table(engine: Engine) -> None:
    sync_table_schema(engine, decision_draft_events_table)
