"""Application-layer tests for LearningService (ATLAS-001 Core Loop).

Exercises the service against real (in-memory) SQLite repositories for
both Evaluation and Learning — not fakes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.learning.capture_learning import (
    CaptureLearningRequest,
    LearningService,
)
from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.exceptions import EvaluationNotFoundError
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.evaluation.value_objects import Statement as EvaluationStatement
from atlas.core.domain.learning.exceptions import LearningNotFoundError
from atlas.core.domain.learning.value_objects import LearningId
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.learning.table import create_learning_table

_EVALUATED_AT = datetime(2026, 10, 15, 9, 0, 0, tzinfo=timezone.utc)
_LEARNED_AT = datetime(2026, 10, 16, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_evaluation_table(eng)
    create_learning_table(eng)
    return eng


@pytest.fixture
def evaluation_repository(engine):
    return SqlAlchemyEvaluationRepository(engine)


@pytest.fixture
def service(engine, evaluation_repository):
    return LearningService(evaluation_repository, SqlAlchemyLearningRepository(engine))


@pytest.fixture
def existing_evaluation(evaluation_repository):
    evaluation = Evaluation.capture(
        outcome_id=OutcomeId(),
        statement=EvaluationStatement("The decision proved correct; demand did accelerate."),
        evaluated_at=_EVALUATED_AT,
    )
    evaluation_repository.add(evaluation)
    return evaluation


def _request(evaluation_id, **overrides) -> CaptureLearningRequest:
    defaults = dict(
        evaluation_id=evaluation_id.value,
        statement="Weigh capex guidance more heavily than headline revenue growth.",
        learned_at=_LEARNED_AT,
        note="Apply this to the next earnings cycle.",
    )
    defaults.update(overrides)
    return CaptureLearningRequest(**defaults)


class TestCapture:
    def test_captures_a_learning_from_an_existing_evaluation(self, service, existing_evaluation):
        learning = service.capture(_request(existing_evaluation.id))
        assert learning.evaluation_id == existing_evaluation.id

    def test_recorded_at_is_assigned_by_atlas(self, service, existing_evaluation):
        before = datetime.now(timezone.utc)
        learning = service.capture(_request(existing_evaluation.id))
        after = datetime.now(timezone.utc)
        assert before <= learning.recorded_at <= after

    def test_rejects_unknown_evaluation(self, service):
        with pytest.raises(EvaluationNotFoundError):
            service.capture(_request(EvaluationId()))

    def test_does_not_write_to_evaluation_repository(
        self, service, evaluation_repository, existing_evaluation
    ):
        before = evaluation_repository.list_all()
        service.capture(_request(existing_evaluation.id))
        after = evaluation_repository.list_all()
        assert before == after


class TestRetrieveById:
    def test_returns_the_captured_learning(self, service, existing_evaluation):
        captured = service.capture(_request(existing_evaluation.id))
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_learning_is_rejected(self, service):
        with pytest.raises(LearningNotFoundError):
            service.get(LearningId())


class TestRetrieveAll:
    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
