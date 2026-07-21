"""Application-layer tests for CaptureDecisionService's Case-context change
(Package R3, Decision Case Context).

Scoped narrowly to the behavior this package adds: `case_id` is required
and is the value ultimately persisted on the Decision. This file does not
attempt to backfill general coverage of `decision_type`/`confidence`/
`subject`/`source` — those remain the deliberately deferred, unresolved
field-set question (Decision-Case-Context-Implementation-Design.md,
Gap G2), untouched by this package.
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
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table

_DECIDED_AT = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def service(repository):
    return CaptureDecisionService(repository)


def _request(**overrides) -> CaptureDecisionRequest:
    defaults = dict(
        case_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        decision_type="BUY",
        subject="ASML",
        reason="Durable moat, undervalued relative to peers",
        confidence=75,
        decided_at=_DECIDED_AT,
    )
    defaults.update(overrides)
    return CaptureDecisionRequest(**defaults)


class TestCaptureDecision:
    def test_case_ownership_is_assigned(self, service):
        case_id = uuid.uuid4()
        decision = service.capture(_request(case_id=case_id))
        assert decision.case_id.value == case_id

    def test_requires_a_case_id(self):
        with pytest.raises(TypeError):
            CaptureDecisionRequest(
                user_id=uuid.uuid4(),
                decision_type="BUY",
                subject="ASML",
                reason="Durable moat, undervalued relative to peers",
                confidence=75,
            )

    def test_decision_can_be_retrieved_with_the_same_case_id(self, service, repository):
        case_id = uuid.uuid4()
        decision = service.capture(_request(case_id=case_id))
        fetched = repository.get(decision.id)
        assert fetched.case_id.value == case_id

    def test_same_reason_in_different_cases_is_permitted(self, service):
        first = service.capture(_request(case_id=uuid.uuid4()))
        second = service.capture(_request(case_id=uuid.uuid4()))
        assert first.case_id != second.case_id
        assert first.id != second.id


class TestServiceDependencySimplification:
    def test_service_depends_only_on_its_own_repository(self):
        import inspect

        signature = inspect.signature(CaptureDecisionService.__init__)
        assert list(signature.parameters) == ["self", "repository"]
