"""Composition root for Decision Review (ATLAS-003).

Wires exactly the four dependencies this review needs: a read-only
DecisionRepository, and the three existing, unmodified Outcome/
Evaluation/Learning services. Does not construct QuestionService or any
of the other First Decision Conversation services — this conversation
starts mid-cycle, not from Question. Does not create the questions/
observations/interpretations/hypotheses/evidence/conclusions tables
either — Decision Review only ever reads Decision, never anything
upstream of it.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.decision_review.orchestrator import DecisionReviewOrchestrator
from atlas.core.application.evaluation.capture_evaluation import EvaluationService
from atlas.core.application.learning.capture_learning import LearningService
from atlas.core.application.outcome.capture_outcome import OutcomeService
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


def create_decision_review_tables(engine: Engine) -> None:
    """Create every table Decision Review needs.

    Includes `decisions` because DecisionRepository needs the table to
    exist to read from it — but this module never creates the questions/
    observations/.../conclusions tables, since Decision Review never
    reads or writes anything upstream of Decision itself.
    """
    create_decision_table(engine)
    create_outcome_table(engine)
    create_evaluation_table(engine)
    create_learning_table(engine)


def build_decision_review_orchestrator(engine: Engine) -> DecisionReviewOrchestrator:
    decision_repository = SqlAlchemyDecisionRepository(engine)
    outcome_repository = SqlAlchemyOutcomeRepository(engine)
    evaluation_repository = SqlAlchemyEvaluationRepository(engine)
    learning_repository = SqlAlchemyLearningRepository(engine)

    return DecisionReviewOrchestrator(
        decision_repository=decision_repository,
        outcome_service=OutcomeService(decision_repository, outcome_repository),
        evaluation_service=EvaluationService(outcome_repository, evaluation_repository),
        learning_service=LearningService(evaluation_repository, learning_repository),
    )
