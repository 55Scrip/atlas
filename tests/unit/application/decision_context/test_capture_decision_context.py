"""Application-layer tests for CaptureDecisionContextService (API-002).

Exercises the cross-aggregate orchestration against real (in-memory)
repositories for both Decision and DecisionContext — not fakes — since the
behavior under test (does a Decision exist? does context already exist?) is
precisely the interaction between the two real repositories.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision_context.capture_decision_context import (
    CaptureDecisionContextRequest,
    CaptureDecisionContextService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.decision_context.exceptions import (
    DecisionNotFoundError,
    DuplicateDecisionContextError,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.decision_context.sqlalchemy_repository import (
    SqlAlchemyDecisionContextRepository,
)
from atlas.core.infrastructure.persistence.decision_context.table import (
    create_decision_context_table,
)

_CAPTURED_AT = datetime(2026, 6, 17, 0, 54, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_decision_context_table(eng)
    return eng


@pytest.fixture
def decision_repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def context_repository(engine):
    return SqlAlchemyDecisionContextRepository(engine)


@pytest.fixture
def service(decision_repository, context_repository):
    return CaptureDecisionContextService(decision_repository, context_repository)


def _existing_decision(decision_repository) -> Decision:
    decision = Decision.register(
        case_id=CaseId(),
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat, undervalued relative to peers"),
        confidence=Confidence(75),
    )
    decision_repository.add(decision)
    return decision


def _request(decision_id: uuid.UUID, **overrides) -> CaptureDecisionContextRequest:
    defaults = dict(
        decision_id=decision_id,
        situation="Large semiconductor exposure already; wanted to preserve cash.",
        captured_at=_CAPTURED_AT,
    )
    defaults.update(overrides)
    return CaptureDecisionContextRequest(**defaults)


class TestCaptureDecisionContext:
    def test_context_can_be_attached_to_an_existing_decision(self, service, decision_repository):
        decision = _existing_decision(decision_repository)

        context = service.capture(_request(decision.id.value))

        assert context.decision_id == decision.id
        assert context.situation.value == (
            "Large semiconductor exposure already; wanted to preserve cash."
        )

    def test_nonexistent_decision_is_rejected(self, service):
        with pytest.raises(DecisionNotFoundError):
            service.capture(_request(uuid.uuid4()))

    def test_duplicate_context_is_rejected(self, service, decision_repository):
        decision = _existing_decision(decision_repository)
        service.capture(_request(decision.id.value))

        with pytest.raises(DuplicateDecisionContextError):
            service.capture(_request(decision.id.value))

    def test_capturing_context_does_not_modify_the_decision(self, service, decision_repository):
        decision = _existing_decision(decision_repository)
        before = decision_repository.get(decision.id)

        service.capture(_request(decision.id.value))

        after = decision_repository.get(decision.id)
        assert after == before
