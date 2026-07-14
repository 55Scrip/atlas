"""Composition root for Pattern Recognition (ATLAS-005).

The only place in this module aware of a SQLAlchemy Engine — reuses
Decision Timeline's own composition (ATLAS-004) unmodified to obtain a
DecisionTimelineQuery; no new table, no new repository.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.decision_timeline.composition import (
    build_decision_timeline_query,
    create_decision_timeline_tables,
)
from atlas.core.application.pattern_recognition.query import PatternRecognitionQuery
from atlas.core.application.pattern_recognition.strategies import (
    SameConfidenceStrategy,
    SameSubjectAndTypeStrategy,
)


def create_pattern_recognition_tables(engine: Engine) -> None:
    """Ensure the tables Pattern Recognition reads from exist.

    Purely a schema-existence concern — Pattern Recognition itself never
    writes a row into any of them.
    """
    create_decision_timeline_tables(engine)


def build_pattern_recognition_query(engine: Engine) -> PatternRecognitionQuery:
    return PatternRecognitionQuery(
        decision_timeline_query=build_decision_timeline_query(engine),
        strategies=(SameSubjectAndTypeStrategy(), SameConfidenceStrategy()),
    )
