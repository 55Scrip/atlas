"""Composition root for Strategy Signature Recognition (ATLAS-006).

The only place in this module aware of a SQLAlchemy Engine — reuses
Pattern Recognition's own composition (ATLAS-005/005B) unmodified to
obtain a PatternRecognitionQuery; no new table, no new repository.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.pattern_recognition.composition import (
    build_pattern_recognition_query,
    create_pattern_recognition_tables,
)
from atlas.core.application.strategy_signature.query import StrategySignatureRecognitionQuery
from atlas.core.application.strategy_signature.strategies import ConnectedPatternsStrategy


def create_strategy_signature_tables(engine: Engine) -> None:
    """Ensure the tables Strategy Signature Recognition reads from exist.

    Purely a schema-existence concern — Strategy Signature Recognition
    itself never writes a row into any of them.
    """
    create_pattern_recognition_tables(engine)


def build_strategy_signature_recognition_query(
    engine: Engine,
) -> StrategySignatureRecognitionQuery:
    return StrategySignatureRecognitionQuery(
        pattern_recognition_query=build_pattern_recognition_query(engine),
        strategies=(ConnectedPatternsStrategy(),),
    )
