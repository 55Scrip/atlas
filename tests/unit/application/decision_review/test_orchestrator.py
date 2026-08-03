"""Unit tests for DecisionReviewOrchestrator (ATLAS-003)."""

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
from atlas.core.application.decision_review import prompts
from atlas.core.application.decision_review.composition import (
    build_decision_review_orchestrator,
    create_decision_review_tables,
)
from atlas.core.application.decision_review.session import DecisionReviewStep
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
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
    service = CaptureDecisionService(
        SqlAlchemyDecisionRepository(engine), SqlAlchemyObservationRepository(engine)
    )
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


class TestListDecisions:
    def test_empty_when_nothing_recorded(self, orchestrator):
        assert orchestrator.list_decisions() == []

    def test_lists_recorded_decisions_numbered_from_one(self, orchestrator, existing_decision):
        numbered = orchestrator.list_decisions()
        assert numbered == [(1, existing_decision)]


class TestSelect:
    def test_valid_selection_creates_a_session_anchored_to_that_decision(
        self, orchestrator, existing_decision
    ):
        numbered = orchestrator.list_decisions()
        session = orchestrator.select(numbered, "1")
        assert session is not None
        assert session.decision_id == existing_decision.id.value
        assert session.current_step is DecisionReviewStep.OUTCOME

    def test_invalid_number_returns_none(self, orchestrator, existing_decision):
        numbered = orchestrator.list_decisions()
        assert orchestrator.select(numbered, "99") is None

    def test_non_numeric_answer_returns_none(self, orchestrator, existing_decision):
        numbered = orchestrator.list_decisions()
        assert orchestrator.select(numbered, "not a number") is None

    def test_does_not_write_to_decision_repository(self, orchestrator, engine, existing_decision):
        decision_repository = SqlAlchemyDecisionRepository(engine)
        before = decision_repository.list_all()
        numbered = orchestrator.list_decisions()
        orchestrator.select(numbered, "1")
        after = decision_repository.list_all()
        assert before == after


def _selected_session(orchestrator, existing_decision):
    numbered = orchestrator.list_decisions()
    return orchestrator.select(numbered, "1")


class TestOutcomeStep:
    def test_captures_outcome_and_advances_to_evaluation(self, orchestrator, existing_decision):
        session = _selected_session(orchestrator, existing_decision)
        turn = orchestrator.respond(session, "Revenue growth accelerated as expected.")
        assert session.current_step is DecisionReviewStep.EVALUATION
        assert session.outcome_id is not None
        assert turn.prompt == prompts.EVALUATION_PROMPT


class TestEvaluationStep:
    def test_captures_evaluation_and_advances_to_learning(self, orchestrator, existing_decision):
        session = _selected_session(orchestrator, existing_decision)
        orchestrator.respond(session, "Revenue growth accelerated as expected.")
        turn = orchestrator.respond(session, "The decision proved correct.")
        assert session.current_step is DecisionReviewStep.LEARNING
        assert session.evaluation_id is not None
        assert turn.prompt == prompts.LEARNING_PROMPT


class TestLearningStep:
    def test_captures_learning_and_completes_the_review(self, orchestrator, existing_decision):
        session = _selected_session(orchestrator, existing_decision)
        orchestrator.respond(session, "Revenue growth accelerated as expected.")
        orchestrator.respond(session, "The decision proved correct.")
        turn = orchestrator.respond(
            session, "Weigh capex guidance more heavily than headline growth."
        )
        assert session.is_complete()
        assert session.learning_id is not None
        assert turn.prompt == prompts.CLOSING_MESSAGE
        assert turn.is_complete
