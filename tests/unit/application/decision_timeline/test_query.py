"""Tests for DecisionTimelineQuery (ATLAS-004).

Constructs DecisionTimelineQuery directly from repository interfaces —
no composition.py, no Engine — proving assembly is independently
testable against whatever repositories are supplied.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.application.decision_timeline.query import DecisionTimelineQuery
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.value_objects import Statement as EvaluationStatement
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.learning.value_objects import Statement as LearningStatement
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
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

_T0 = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_outcome_table(eng)
    create_evaluation_table(eng)
    create_learning_table(eng)
    return eng


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def outcome_repository(engine):
    return SqlAlchemyOutcomeRepository(engine)


@pytest.fixture
def evaluation_repository(engine):
    return SqlAlchemyEvaluationRepository(engine)


@pytest.fixture
def learning_repository(engine):
    return SqlAlchemyLearningRepository(engine)


@pytest.fixture
def query(decision_repository, outcome_repository, evaluation_repository, learning_repository):
    return DecisionTimelineQuery(
        decision_repository, outcome_repository, evaluation_repository, learning_repository
    )


def _make_decision(decision_repository, decided_at, subject="NVIDIA"):
    service = CaptureDecisionService(decision_repository)
    return service.capture(
        CaptureDecisionRequest(
            case_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            decision_type="BUY",
            subject=subject,
            reason="Demand is accelerating.",
            confidence=80,
            decided_at=decided_at,
        )
    )


def _make_outcome(outcome_repository, decision_id, recorded_at):
    outcome = Outcome.capture(
        case_id=CaseId(),
        decision_id=decision_id,
        statement=OutcomeStatement("Revenue grew as expected."),
        occurred_at=_T0,
        clock=lambda: recorded_at,
    )
    outcome_repository.add(outcome)
    return outcome


def _make_evaluation(evaluation_repository, outcome_id, recorded_at, statement="On track."):
    evaluation = Evaluation.capture(
        outcome_id=outcome_id,
        statement=EvaluationStatement(statement),
        evaluated_at=_T0,
        clock=lambda: recorded_at,
    )
    evaluation_repository.add(evaluation)
    return evaluation


def _make_learning(learning_repository, evaluation_id, recorded_at, statement="Noted."):
    learning = Learning.capture(
        evaluation_id=evaluation_id,
        statement=LearningStatement(statement),
        learned_at=_T0,
        clock=lambda: recorded_at,
    )
    learning_repository.add(learning)
    return learning


class TestEmptyTimeline:
    def test_no_decisions_yields_no_entries(self, query):
        assert query.build().entries == ()


class TestDecisionOrdering:
    def test_decisions_ordered_by_decided_at_ascending(self, decision_repository, query):
        _make_decision(decision_repository, _T0 + timedelta(days=2), subject="Later")
        _make_decision(decision_repository, _T0, subject="Earlier")
        _make_decision(decision_repository, _T0 + timedelta(days=1), subject="Middle")

        timeline = query.build()

        subjects = [entry.decision.subject.value for entry in timeline.entries]
        assert subjects == ["Earlier", "Middle", "Later"]

    def test_decisions_with_identical_decided_at_are_tie_broken_by_id(
        self, decision_repository, query
    ):
        first = _make_decision(decision_repository, _T0, subject="A")
        second = _make_decision(decision_repository, _T0, subject="B")

        timeline = query.build()

        expected_order = sorted([first, second], key=lambda d: d.id.value)
        assert [entry.decision.id for entry in timeline.entries] == [d.id for d in expected_order]


class TestReviewChainNesting:
    def test_decision_with_no_outcomes_has_empty_review_chains(self, decision_repository, query):
        _make_decision(decision_repository, _T0)
        timeline = query.build()
        assert timeline.entries[0].review_chains == ()

    def test_multiple_outcomes_ordered_by_recorded_at(
        self, decision_repository, outcome_repository, query
    ):
        decision = _make_decision(decision_repository, _T0)
        later_outcome = _make_outcome(outcome_repository, decision.id, _T0 + timedelta(hours=2))
        earlier_outcome = _make_outcome(outcome_repository, decision.id, _T0)

        timeline = query.build()

        chains = timeline.entries[0].review_chains
        assert [chain.outcome.id for chain in chains] == [earlier_outcome.id, later_outcome.id]

    def test_outcome_with_no_evaluations_has_empty_evaluations_tuple(
        self, decision_repository, outcome_repository, query
    ):
        decision = _make_decision(decision_repository, _T0)
        _make_outcome(outcome_repository, decision.id, _T0)

        timeline = query.build()

        assert timeline.entries[0].review_chains[0].evaluations == ()


class TestMultipleEvaluationsPerOutcomeAreAllPreserved:
    def test_two_evaluations_for_the_same_outcome_both_appear_correctly_ordered(
        self, decision_repository, outcome_repository, evaluation_repository, query
    ):
        decision = _make_decision(decision_repository, _T0)
        outcome = _make_outcome(outcome_repository, decision.id, _T0)
        later_evaluation = _make_evaluation(
            evaluation_repository, outcome.id, _T0 + timedelta(hours=2), statement="Second look."
        )
        earlier_evaluation = _make_evaluation(
            evaluation_repository, outcome.id, _T0 + timedelta(hours=1), statement="First look."
        )

        timeline = query.build()

        evaluations = timeline.entries[0].review_chains[0].evaluations
        assert len(evaluations) == 2
        assert [e.evaluation.id for e in evaluations] == [
            earlier_evaluation.id,
            later_evaluation.id,
        ]

    def test_evaluation_with_no_learnings_has_empty_learnings_tuple(
        self, decision_repository, outcome_repository, evaluation_repository, query
    ):
        decision = _make_decision(decision_repository, _T0)
        outcome = _make_outcome(outcome_repository, decision.id, _T0)
        _make_evaluation(evaluation_repository, outcome.id, _T0)

        timeline = query.build()

        assert timeline.entries[0].review_chains[0].evaluations[0].learnings == ()


class TestMultipleLearningsPerEvaluationAreAllPreserved:
    def test_two_learnings_for_the_same_evaluation_both_appear_correctly_ordered(
        self,
        decision_repository,
        outcome_repository,
        evaluation_repository,
        learning_repository,
        query,
    ):
        decision = _make_decision(decision_repository, _T0)
        outcome = _make_outcome(outcome_repository, decision.id, _T0)
        evaluation = _make_evaluation(evaluation_repository, outcome.id, _T0)
        later_learning = _make_learning(
            learning_repository, evaluation.id, _T0 + timedelta(hours=2), statement="Second."
        )
        earlier_learning = _make_learning(
            learning_repository, evaluation.id, _T0 + timedelta(hours=1), statement="First."
        )

        timeline = query.build()

        learnings = timeline.entries[0].review_chains[0].evaluations[0].learnings
        assert len(learnings) == 2
        assert [learning.id for learning in learnings] == [
            earlier_learning.id,
            later_learning.id,
        ]


class TestNeverWrites:
    def test_build_never_calls_add_on_any_repository(
        self, decision_repository, outcome_repository, evaluation_repository, learning_repository
    ):
        class RaisingOnAdd:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def add(self, *args, **kwargs):
                raise AssertionError("DecisionTimelineQuery must never write")

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

        decision = _make_decision(decision_repository, _T0)
        outcome = _make_outcome(outcome_repository, decision.id, _T0)
        evaluation = _make_evaluation(evaluation_repository, outcome.id, _T0)
        _make_learning(learning_repository, evaluation.id, _T0)

        spy_query = DecisionTimelineQuery(
            RaisingOnAdd(decision_repository),
            RaisingOnAdd(outcome_repository),
            RaisingOnAdd(evaluation_repository),
            RaisingOnAdd(learning_repository),
        )

        spy_query.build()  # must not raise
