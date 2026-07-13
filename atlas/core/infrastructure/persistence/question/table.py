"""SQL schema for the Question store.

Own MetaData, no foreign keys — Question is the root of the Core Loop.
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

questions_table = Table(
    "questions",
    metadata,
    Column("question_id", String, primary_key=True),
    Column("statement", String, nullable=False),
    Column("note", String, nullable=True),
    Column("raised_at", String, nullable=False),
    Column("recorded_at", String, nullable=False),
)


def create_question_table(engine: Engine) -> None:
    metadata.create_all(engine, tables=[questions_table])
