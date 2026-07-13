"""SQL schema for the Interpretation store.

Own MetaData, no SQL ForeignKey — observation_id is a plain indexed
string column, matching the rest of this codebase's convention.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

interpretations_table = Table(
    "interpretations",
    metadata,
    Column("interpretation_id", String, primary_key=True),
    Column("observation_id", String, nullable=False, index=True),
    Column("statement", String, nullable=False),
    Column("note", String, nullable=True),
    Column("interpreted_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_interpretation_table(engine: Engine) -> None:
    metadata.create_all(engine, tables=[interpretations_table])
