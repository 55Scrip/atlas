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
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.exceptions import (
    CrossCaseObservationError,
    ObservationNotFoundError,
)
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement, Subject
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table

_DECIDED_AT = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(eng)
    create_observation_table(eng)
    return eng


@pytest.fixture
def repository(engine):
    return SqlAlchemyDecisionRepository(engine)


@pytest.fixture
def observation_repository(engine):
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def service(repository, observation_repository):
    return CaptureDecisionService(repository, observation_repository)


def _seed_observation(observation_repository, *, case_id: uuid.UUID) -> uuid.UUID:
    observation = Observation.capture(
        case_id=CaseId(case_id),
        subject=Subject("Semiconductor sector"),
        statement=Statement("Capex guidance raised."),
        observed_at=_DECIDED_AT,
    )
    observation_repository.add(observation)
    return observation.id.value


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
    def test_service_depends_on_its_repository_and_observation_repository(self):
        import inspect

        signature = inspect.signature(CaptureDecisionService.__init__)
        assert list(signature.parameters) == ["self", "repository", "observation_repository"]


class TestObservationAnchor:
    def test_decision_captured_with_no_observation_id_has_none(self, service):
        decision = service.capture(_request(observation_id=None))
        assert decision.observation_id is None

    def test_decision_can_be_anchored_to_an_existing_same_case_observation(
        self, service, observation_repository
    ):
        case_id = uuid.uuid4()
        observation_id = _seed_observation(observation_repository, case_id=case_id)

        decision = service.capture(_request(case_id=case_id, observation_id=observation_id))

        assert decision.observation_id.value == observation_id

    def test_rejects_a_nonexistent_observation_id(self, service):
        with pytest.raises(ObservationNotFoundError):
            service.capture(_request(observation_id=uuid.uuid4()))

    def test_rejects_an_observation_from_a_different_case(self, service, observation_repository):
        other_case_id = uuid.uuid4()
        observation_id = _seed_observation(observation_repository, case_id=other_case_id)

        with pytest.raises(CrossCaseObservationError):
            service.capture(_request(case_id=uuid.uuid4(), observation_id=observation_id))

    def test_no_decision_is_persisted_when_the_observation_check_fails(self, service, repository):
        with pytest.raises(ObservationNotFoundError):
            service.capture(_request(observation_id=uuid.uuid4()))
        assert repository.list_all() == []
