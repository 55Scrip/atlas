"""SQL schema for the reasoning_link module (ATLAS-001 Core Loop).

PROVISIONAL STATUS: see atlas.core.domain.reasoning_link.entity's module
docstring — this whole module, tables included, is a temporary
orchestration mechanism, not a permanent schema commitment.

One shared MetaData for all four link tables, since reasoning_link is
one bounded context housing four small, structurally identical
aggregates — matching this codebase's "one module = one MetaData"
convention at the module level. No SQL ForeignKey anywhere (matching
every other module in this codebase); no unique=True anywhere (none of
these four edges is 1:1).
"""
from __future__ import annotations

from sqlalchemy import Column, MetaData, String, Table
from sqlalchemy.engine import Engine

metadata = MetaData()

question_observation_links_table = Table(
    "question_observation_links",
    metadata,
    Column("link_id", String, primary_key=True),
    Column("question_id", String, nullable=False, index=True),
    Column("observation_id", String, nullable=False, index=True),
    Column("linked_at", String, nullable=False),
)

interpretation_hypothesis_links_table = Table(
    "interpretation_hypothesis_links",
    metadata,
    Column("link_id", String, primary_key=True),
    Column("interpretation_id", String, nullable=False, index=True),
    Column("hypothesis_id", String, nullable=False, index=True),
    Column("linked_at", String, nullable=False),
)

hypothesis_evidence_links_table = Table(
    "hypothesis_evidence_links",
    metadata,
    Column("link_id", String, primary_key=True),
    Column("hypothesis_id", String, nullable=False, index=True),
    Column("evidence_id", String, nullable=False, index=True),
    Column("linked_at", String, nullable=False),
)

conclusion_decision_links_table = Table(
    "conclusion_decision_links",
    metadata,
    Column("link_id", String, primary_key=True),
    Column("conclusion_id", String, nullable=False, index=True),
    Column("decision_id", String, nullable=False, index=True),
    Column("linked_at", String, nullable=False),
)


def create_reasoning_link_tables(engine: Engine) -> None:
    metadata.create_all(
        engine,
        tables=[
            question_observation_links_table,
            interpretation_hypothesis_links_table,
            hypothesis_evidence_links_table,
            conclusion_decision_links_table,
        ],
    )
