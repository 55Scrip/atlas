"""End-to-end proof of Decision Review (ATLAS-003).

Scripts a full review (selection through Learning), verifies two
independent reviews of the same Decision each produce their own valid
triple, and explicitly verifies the documented limitation: an
interrupted review leaves an orphaned Outcome with no Evaluation or
Learning, and ATLAS-003 does not detect, resume, or repair that.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.application.decision_review.composition import (
    build_decision_review_orchestrator,
    create_decision_review_tables,
)
from atlas.core.application.decision_review.session import DecisionReviewStep
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.value_objects import LearningId
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)

_DECIDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_review_tables(eng)
    return eng


@pytest.fixture
def orchestrator(engine):
    return build_decision_review_orchestrator(engine)


@pytest.fixture
def existing_decision(engine):
    service = CaptureDecisionService(SqlAlchemyDecisionRepository(engine))
    return service.capture(
        CaptureDecisionRequest(
            case_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            decision_type="BUY",
            subject="NVIDIA",
            reason="Demand for AI infrastructure is accelerating.",
            confidence=80,
            decided_at=_DECIDED_AT,
        )
    )


def _run_full_review(orchestrator, decision):
    numbered = orchestrator.list_decisions()
    session = orchestrator.select(numbered, "1")
    orchestrator.respond(session, "Revenue growth accelerated as expected.")
    orchestrator.respond(session, "The decision proved correct.")
    orchestrator.respond(session, "Weigh capex guidance more heavily than headline growth.")
    return session


class TestCompleteReview:
    def test_walks_selection_through_learning(self, engine, orchestrator, existing_decision):
        session = _run_full_review(orchestrator, existing_decision)

        assert session.is_complete()
        assert session.current_step is DecisionReviewStep.REVIEW_RECORDED
        assert session.decision_id == existing_decision.id.value

        outcome_repo = SqlAlchemyOutcomeRepository(engine)
        evaluation_repo = SqlAlchemyEvaluationRepository(engine)
        learning_repo = SqlAlchemyLearningRepository(engine)

        outcome = outcome_repo.get(OutcomeId(session.outcome_id))
        evaluation = evaluation_repo.get(EvaluationId(session.evaluation_id))
        learning = learning_repo.get(LearningId(session.learning_id))

        assert outcome.decision_id.value == existing_decision.id.value
        assert evaluation.outcome_id == outcome.id
        assert learning.evaluation_id == evaluation.id

    def test_decision_itself_is_never_written_to(self, engine, orchestrator, existing_decision):
        decision_repo = SqlAlchemyDecisionRepository(engine)
        before = decision_repo.list_all()
        _run_full_review(orchestrator, existing_decision)
        after = decision_repo.list_all()
        assert before == after


class TestMultipleReviewsOfTheSameDecision:
    def test_two_reviews_produce_two_independent_triples(
        self, engine, orchestrator, existing_decision
    ):
        first_session = _run_full_review(orchestrator, existing_decision)
        second_session = _run_full_review(orchestrator, existing_decision)

        assert first_session.decision_id == second_session.decision_id
        assert first_session.outcome_id != second_session.outcome_id
        assert first_session.evaluation_id != second_session.evaluation_id
        assert first_session.learning_id != second_session.learning_id

        outcome_repo = SqlAlchemyOutcomeRepository(engine)
        outcomes_for_decision = outcome_repo.list_by_decision_id(existing_decision.id)
        assert len(outcomes_for_decision) == 2


class TestInterruptedReviewIsNotRepaired:
    def test_stopping_after_outcome_leaves_an_orphaned_outcome(
        self, engine, orchestrator, existing_decision
    ):
        numbered = orchestrator.list_decisions()
        session = orchestrator.select(numbered, "1")
        orchestrator.respond(session, "Revenue growth accelerated as expected.")
        # The person stops here — no Evaluation, no Learning.

        assert session.current_step is DecisionReviewStep.EVALUATION
        assert not session.is_complete()

        outcome_repo = SqlAlchemyOutcomeRepository(engine)
        evaluation_repo = SqlAlchemyEvaluationRepository(engine)
        learning_repo = SqlAlchemyLearningRepository(engine)

        outcome = outcome_repo.get(OutcomeId(session.outcome_id))
        assert outcome is not None
        assert evaluation_repo.list_by_outcome_id(outcome.id) == []
        assert learning_repo.list_all() == []

    def test_reviewing_again_produces_a_second_unrelated_outcome(
        self, engine, orchestrator, existing_decision
    ):
        numbered = orchestrator.list_decisions()
        interrupted_session = orchestrator.select(numbered, "1")
        orchestrator.respond(interrupted_session, "Revenue growth accelerated as expected.")

        # ATLAS-003 does not detect or resume the interrupted review above —
        # a fresh review starts an entirely new, independent triple.
        fresh_session = _run_full_review(orchestrator, existing_decision)

        assert fresh_session.outcome_id != interrupted_session.outcome_id
        assert fresh_session.is_complete()

        outcome_repo = SqlAlchemyOutcomeRepository(engine)
        outcomes_for_decision = outcome_repo.list_by_decision_id(existing_decision.id)
        assert len(outcomes_for_decision) == 2
