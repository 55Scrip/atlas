"""SQL schema for the Observation store.

Own MetaData, no foreign keys — Observation introduces no relationship to
Decision, DecisionContext, or any other aggregate.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

observations_table = Table(
    "observations",
    metadata,
    Column("observation_id", String, primary_key=True),
    Column("case_id", String, nullable=False, index=True),
    Column("subject", String, nullable=False),
    Column("statement", String, nullable=False),
    Column("source", String, nullable=True),
    Column("note", String, nullable=True),
    Column("observed_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_observation_table(engine: Engine) -> None:
    metadata.create_all(engine, tables=[observations_table])
