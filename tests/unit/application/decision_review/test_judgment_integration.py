"""Tests for Judgment capture from Evaluation (Package M2,
Evaluation-to-Judgment-Reduction-Design.md, Section 23).

Covers exactly what the package requires: success-path semantic mapping,
ordering relative to Learning success, the failure boundary (Judgment
capture failing must never retry Outcome, Evaluation, or Learning),
at-most-once behavior, exact-identity propagation of the review's own
Outcome, and composition wiring. Uses the same in-memory-SQLite fixture
idiom already established by test_orchestrator.py and
test_reasoning_trace_integration.py — never the real on-disk database.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
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
from atlas.core.application.judgment.capture_judgment import JudgmentService
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import evaluations_table
from atlas.core.infrastructure.persistence.judgment.table import judgments_table
from atlas.core.infrastructure.persistence.learning.table import learnings_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import outcomes_table

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


def _judgment_rows(engine):
    with engine.connect() as connection:
        return connection.execute(select(judgments_table)).fetchall()


def _outcome_case_id(engine, outcome_id):
    outcome = SqlAlchemyOutcomeRepository(engine).get(outcome_id)
    return outcome.case_id.value


def _run_full_review(orchestrator, evaluation_statement="The decision proved correct."):
    numbered = orchestrator.list_decisions()
    session = orchestrator.select(numbered, "1")
    orchestrator.respond(session, "Revenue growth accelerated as expected.")
    orchestrator.respond(session, evaluation_statement)
    turn = orchestrator.respond(
        session, "Weigh capex guidance more heavily than headline growth."
    )
    return session, turn


class _FailingJudgmentService:
    """A fake standing in for JudgmentService that always raises,
    counting how many times capture() is attempted.
    """

    def __init__(self) -> None:
        self.capture_calls = 0

    def capture(self, request):
        self.capture_calls += 1
        raise RuntimeError("simulated Judgment capture failure")


class TestSuccessfulSemanticMapping:
    def test_exactly_one_judgment_created_with_exact_mapping(
        self, orchestrator, engine, existing_decision
    ):
        session, turn = _run_full_review(orchestrator)

        assert turn.prompt == prompts.CLOSING_MESSAGE
        assert turn.is_complete
        assert session.current_step is DecisionReviewStep.REVIEW_RECORDED

        rows = _judgment_rows(engine)
        assert len(rows) == 1
        judgment_id, case_id, characterization, target_type, target_id, recorded_at = rows[0]

        assert characterization == "The decision proved correct."
        assert target_type == DomainObjectType.OUTCOME.value
        assert target_id == str(session.outcome_id)
        assert case_id == str(_outcome_case_id(engine, OutcomeId(session.outcome_id)))

    def test_note_and_learning_content_are_not_included(
        self, orchestrator, engine, existing_decision
    ):
        session, _ = _run_full_review(orchestrator)
        rows = _judgment_rows(engine)
        characterization = rows[0][2]
        assert "capex" not in characterization
        assert characterization == "The decision proved correct."

    def test_evaluation_timestamps_are_not_used_as_judgment_recorded_at(
        self, orchestrator, engine, existing_decision
    ):
        session, _ = _run_full_review(orchestrator)
        evaluation = SqlAlchemyEvaluationRepository(engine).get(
            EvaluationId(session.evaluation_id)
        )
        rows = _judgment_rows(engine)
        judgment_recorded_at = rows[0][5]
        assert judgment_recorded_at != evaluation.evaluated_at.isoformat()
        assert judgment_recorded_at != evaluation.recorded_at.isoformat()

    def test_legacy_review_completes_normally(self, orchestrator, existing_decision):
        session, turn = _run_full_review(orchestrator)
        assert session.is_complete()
        assert session.outcome_id is not None
        assert session.evaluation_id is not None
        assert session.learning_id is not None


class TestOrdering:
    def test_no_judgment_before_evaluation_success(
        self, orchestrator, engine, existing_decision
    ):
        numbered = orchestrator.list_decisions()
        session = orchestrator.select(numbered, "1")
        orchestrator.respond(session, "Revenue growth accelerated as expected.")
        assert _judgment_rows(engine) == []

    def test_no_judgment_before_learning_success(
        self, orchestrator, engine, existing_decision
    ):
        numbered = orchestrator.list_decisions()
        session = orchestrator.select(numbered, "1")
        orchestrator.respond(session, "Revenue growth accelerated as expected.")
        orchestrator.respond(session, "The decision proved correct.")
        assert _judgment_rows(engine) == []

    def test_outcome_evaluation_learning_committed_even_if_judgment_fails(
        self, orchestrator, engine, existing_decision
    ):
        orchestrator._judgment_service = _FailingJudgmentService()
        session, turn = _run_full_review(orchestrator)

        assert session.outcome_id is not None
        assert session.evaluation_id is not None
        assert session.learning_id is not None
        assert session.current_step is DecisionReviewStep.REVIEW_RECORDED
        assert turn.prompt == prompts.CLOSING_MESSAGE_JUDGMENT_FAILED
        assert turn.is_complete


class TestFailureBoundary:
    def test_failure_is_surfaced_and_no_judgment_persisted(
        self, orchestrator, engine, existing_decision
    ):
        fake_service = _FailingJudgmentService()
        orchestrator._judgment_service = fake_service

        session, turn = _run_full_review(orchestrator)

        assert fake_service.capture_calls == 1
        assert turn.prompt == prompts.CLOSING_MESSAGE_JUDGMENT_FAILED
        assert _judgment_rows(engine) == []

    def test_outcome_evaluation_learning_each_invoked_exactly_once(
        self, orchestrator, engine, existing_decision
    ):
        orchestrator._judgment_service = _FailingJudgmentService()
        _run_full_review(orchestrator)

        with engine.connect() as connection:
            assert len(connection.execute(select(outcomes_table)).fetchall()) == 1
            assert len(connection.execute(select(evaluations_table)).fetchall()) == 1
            assert len(connection.execute(select(learnings_table)).fetchall()) == 1

    def test_no_retry_path_exists_after_judgment_failure(self, orchestrator, existing_decision):
        orchestrator._judgment_service = _FailingJudgmentService()
        session, _ = _run_full_review(orchestrator)

        with pytest.raises(KeyError):
            orchestrator.respond(session, "anything")


class TestAtMostOnce:
    def test_successful_review_creates_exactly_one_judgment(
        self, orchestrator, engine, existing_decision
    ):
        _run_full_review(orchestrator)
        assert len(_judgment_rows(engine)) == 1

    def test_reentering_after_terminal_state_does_not_create_another(
        self, orchestrator, engine, existing_decision
    ):
        session, _ = _run_full_review(orchestrator)
        with pytest.raises(KeyError):
            orchestrator.respond(session, "irrelevant")
        assert len(_judgment_rows(engine)) == 1

    def test_reprompt_during_evaluation_input_creates_no_judgment(
        self, orchestrator, engine, existing_decision
    ):
        numbered = orchestrator.list_decisions()
        session = orchestrator.select(numbered, "1")
        orchestrator.respond(session, "Revenue growth accelerated as expected.")
        orchestrator.respond(session, "The decision proved correct.")
        assert _judgment_rows(engine) == []

    def test_two_independent_reviews_each_get_their_own_judgment(
        self, orchestrator, engine, existing_decision
    ):
        _run_full_review(orchestrator)
        _run_full_review(orchestrator)
        assert len(_judgment_rows(engine)) == 2


class TestIdentityPropagation:
    def test_judgment_references_the_exact_outcome_from_this_review(
        self, orchestrator, engine, existing_decision
    ):
        session, _ = _run_full_review(orchestrator)
        rows = _judgment_rows(engine)
        assert rows[0][4] == str(session.outcome_id)

    def test_two_reviews_reference_their_own_distinct_outcomes(
        self, orchestrator, engine, existing_decision
    ):
        session_one, _ = _run_full_review(orchestrator)
        session_two, _ = _run_full_review(orchestrator)

        assert session_one.outcome_id != session_two.outcome_id
        rows = _judgment_rows(engine)
        target_ids = {row[4] for row in rows}
        assert target_ids == {str(session_one.outcome_id), str(session_two.outcome_id)}


class TestComposition:
    def test_real_composition_supplies_a_judgment_service(self, orchestrator):
        assert isinstance(orchestrator._judgment_service, JudgmentService)

    def test_uses_in_memory_database_not_the_real_repository_file(self, engine):
        assert str(engine.url) == "sqlite:///:memory:"
