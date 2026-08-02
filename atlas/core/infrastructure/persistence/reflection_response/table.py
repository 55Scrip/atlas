"""SQL schema for the ReflectionResponse Store (ATLAS-009).

Own MetaData, mirroring every other bounded context in this codebase.
The nested provenance data (grounding_pattern, strategy_signature_patterns)
is variable-length and write-once/rarely-read (ATLAS-009-D §12, read
isolation from every other capability) — JSON-encoded text columns are
the smallest adequate serialization, not a new relational schema for
data nobody joins against.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.engine import Engine

from atlas.core.infrastructure.persistence.shared.schema_sync import sync_table_schema

metadata = MetaData()

reflection_responses_table = Table(
    "reflection_responses",
    metadata,
    Column("id", String, primary_key=True),
    Column("decision_id", String, nullable=False, index=True),
    Column("response_text", String, nullable=False),
    Column("reflection_description", String, nullable=False),
    Column("coaching_question_text", String, nullable=False),
    Column("grounding_pattern_json", String, nullable=False),
    Column("strategy_signature_patterns_json", String, nullable=False),
    Column("reasoning_context_subject", String, nullable=True),
    Column("reasoning_context_decision_type", String, nullable=True),
    Column("reasoning_context_confidence", Integer, nullable=True),
    Column("recorded_at", String, nullable=False),
)


def create_reflection_response_table(engine: Engine) -> None:
    sync_table_schema(engine, reflection_responses_table)
