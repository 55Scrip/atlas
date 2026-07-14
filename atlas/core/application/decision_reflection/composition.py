"""Composition root for Decision Reflection (ATLAS-007).

The only place in this module aware of a SQLAlchemy Engine — reuses
Pattern Recognition's and Strategy Signature Recognition's own
composition (ATLAS-005/005B/006) unmodified; no new table, no new
repository.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.decision_reflection.query import DecisionReflectionQuery
from atlas.core.application.pattern_recognition.composition import (
    build_pattern_recognition_query,
)
from atlas.core.application.strategy_signature.composition import (
    build_strategy_signature_recognition_query,
    create_strategy_signature_tables,
)


def create_decision_reflection_tables(engine: Engine) -> None:
    """Ensure the tables Decision Reflection reads from exist.

    Purely a schema-existence concern — Decision Reflection itself never
    writes a row into any of them.
    """
    create_strategy_signature_tables(engine)


def build_decision_reflection_query(engine: Engine) -> DecisionReflectionQuery:
    return DecisionReflectionQuery(
        pattern_recognition_query=build_pattern_recognition_query(engine),
        strategy_signature_recognition_query=build_strategy_signature_recognition_query(engine),
    )
