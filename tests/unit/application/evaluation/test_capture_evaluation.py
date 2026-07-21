"""Application-layer tests for EvaluationService (ATLAS-001 Core Loop).

Exercises the service against real (in-memory) SQLite repositories for
both Outcome and Evaluation — not fakes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.evaluation.capture_evaluation import (
    CaptureEvaluationRequest,
    EvaluationService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.evaluation.exceptions import EvaluationNotFoundError
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.exceptions import OutcomeNotFoundError
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.domain.outcome.value_objects import Statement as OutcomeStatement
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_OCCURRED_AT = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
_EVALUATED_AT = datetime(2026, 10, 15, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_outcome_table(eng)
    create_evaluation_table(eng)
    return eng


@pytest.fixture
def outcome_repository(engine):
    return SqlAlchemyOutcomeRepository(engine)


@pytest.fixture
def service(engine, outcome_repository):
    return EvaluationService(outcome_repository, SqlAlchemyEvaluationRepository(engine))


@pytest.fixture
def existing_outcome(outcome_repository):
    outcome = Outcome.capture(
        case_id=CaseId(),
        decision_id=DecisionId(),
        statement=OutcomeStatement("Revenue growth accelerated as expected."),
        occurred_at=_OCCURRED_AT,
    )
    outcome_repository.add(outcome)
    return outcome


def _request(outcome_id, **overrides) -> CaptureEvaluationRequest:
    defaults = dict(
        outcome_id=outcome_id.value,
        statement="The decision proved correct; demand did accelerate.",
        evaluated_at=_EVALUATED_AT,
        note="Consistent with the original thesis.",
    )
    defaults.update(overrides)
    return CaptureEvaluationRequest(**defaults)


class TestCapture:
    def test_captures_an_evaluation_of_an_existing_outcome(self, service, existing_outcome):
        evaluation = service.capture(_request(existing_outcome.id))
        assert evaluation.outcome_id == existing_outcome.id

    def test_recorded_at_is_assigned_by_atlas(self, service, existing_outcome):
        before = datetime.now(timezone.utc)
        evaluation = service.capture(_request(existing_outcome.id))
        after = datetime.now(timezone.utc)
        assert before <= evaluation.recorded_at <= after

    def test_rejects_unknown_outcome(self, service):
        with pytest.raises(OutcomeNotFoundError):
            service.capture(_request(OutcomeId()))

    def test_does_not_write_to_outcome_repository(
        self, service, outcome_repository, existing_outcome
    ):
        before = outcome_repository.list_all()
        service.capture(_request(existing_outcome.id))
        after = outcome_repository.list_all()
        assert before == after


class TestRetrieveById:
    def test_returns_the_captured_evaluation(self, service, existing_outcome):
        captured = service.capture(_request(existing_outcome.id))
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_evaluation_is_rejected(self, service):
        with pytest.raises(EvaluationNotFoundError):
            service.get(EvaluationId())


class TestRetrieveAll:
    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
