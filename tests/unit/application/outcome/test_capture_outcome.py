"""Application-layer tests for OutcomeService (ATLAS-001 Core Loop).

Exercises the service against real (in-memory) SQLite repositories for
both Decision and Outcome — not fakes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.outcome.capture_outcome import (
    CaptureOutcomeRequest,
    OutcomeService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionId,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.outcome.exceptions import DecisionNotFoundError, OutcomeNotFoundError
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table

_DECIDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
_OCCURRED_AT = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))


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
    return eng


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def service(engine, decision_repository):
    return OutcomeService(decision_repository, SqlAlchemyOutcomeRepository(engine))


@pytest.fixture
def existing_decision(decision_repository):
    decision = Decision.register(
        case_id=CaseId(),
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("NVIDIA"),
        investment_case=InvestmentCase("Demand for AI infrastructure is accelerating."),
        confidence=Confidence(80),
        decided_at=_DECIDED_AT,
    )
    decision_repository.add(decision)
    return decision


def _request(decision_id, **overrides) -> CaptureOutcomeRequest:
    defaults = dict(
        decision_id=decision_id.value,
        statement="Revenue growth accelerated as expected.",
        occurred_at=_OCCURRED_AT,
        note="Confirmed by the following quarter's report.",
    )
    defaults.update(overrides)
    return CaptureOutcomeRequest(**defaults)


class TestCapture:
    def test_captures_an_outcome_of_an_existing_decision(self, service, existing_decision):
        outcome = service.capture(_request(existing_decision.id))
        assert outcome.decision_id == existing_decision.id
        assert outcome.case_id == existing_decision.case_id

    def test_recorded_at_is_assigned_by_atlas(self, service, existing_decision):
        before = datetime.now(timezone.utc)
        outcome = service.capture(_request(existing_decision.id))
        after = datetime.now(timezone.utc)
        assert before <= outcome.recorded_at <= after

    def test_rejects_unknown_decision(self, service):
        with pytest.raises(DecisionNotFoundError):
            service.capture(_request(DecisionId()))

    def test_does_not_write_to_decision_repository(
        self, service, decision_repository, existing_decision
    ):
        before = decision_repository.list_all()
        service.capture(_request(existing_decision.id))
        after = decision_repository.list_all()
        assert before == after


class TestRetrieveById:
    def test_returns_the_captured_outcome(self, service, existing_decision):
        captured = service.capture(_request(existing_decision.id))
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_outcome_is_rejected(self, service):
        with pytest.raises(OutcomeNotFoundError):
            service.get(OutcomeId())


class TestRetrieveAll:
    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
