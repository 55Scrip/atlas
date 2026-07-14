"""Composition root for Decision Timeline (ATLAS-004).

The only place in this module aware of a SQLAlchemy Engine —
DecisionTimelineQuery itself depends only on repository interfaces.
Reuses the same four tables Decision Review already reads/writes; no new
table, no new repository method.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.decision_timeline.query import DecisionTimelineQuery
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.learning.table import create_learning_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table


def create_decision_timeline_tables(engine: Engine) -> None:
    """Ensure the tables Decision Timeline reads from exist.

    Purely a schema-existence concern — Timeline itself never writes a
    row into any of them.
    """
    create_decision_table(engine)
    create_outcome_table(engine)
    create_evaluation_table(engine)
    create_learning_table(engine)


def build_decision_timeline_query(engine: Engine) -> DecisionTimelineQuery:
    return DecisionTimelineQuery(
        decision_repository=SqlAlchemyDecisionRepository(engine),
        outcome_repository=SqlAlchemyOutcomeRepository(engine),
        evaluation_repository=SqlAlchemyEvaluationRepository(engine),
        learning_repository=SqlAlchemyLearningRepository(engine),
    )
