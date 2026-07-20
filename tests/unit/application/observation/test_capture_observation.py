"""Application-layer tests for CaptureObservationService (API-003).

Uses a real (in-memory) repository — not a fake — since even a simple,
single-repository service is worth verifying end-to-end against genuine
persistence, matching the pattern established for API-001/002.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.observation.capture_observation import (
    CaptureObservationRequest,
    CaptureObservationService,
)
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table

_OBSERVED_AT = datetime(2026, 7, 13, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_observation_table(engine)
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def service(repository):
    return CaptureObservationService(repository)


def _request(**overrides) -> CaptureObservationRequest:
    defaults = dict(
        case_id=uuid.uuid4(),
        subject="Semiconductor sector",
        statement="Several semiconductor companies raised guidance.",
        observed_at=_OBSERVED_AT,
    )
    defaults.update(overrides)
    return CaptureObservationRequest(**defaults)


class TestCaptureObservation:
    def test_observation_can_be_captured(self, service):
        observation = service.capture(_request())
        assert observation.subject.value == "Semiconductor sector"
        assert observation.statement.value == "Several semiconductor companies raised guidance."

    def test_case_ownership_is_assigned(self, service):
        case_id = uuid.uuid4()
        observation = service.capture(_request(case_id=case_id))
        assert observation.case_id.value == case_id

    def test_recorded_at_is_assigned_by_atlas_not_the_caller(self, service):
        before = datetime.now(timezone.utc)
        observation = service.capture(_request())
        after = datetime.now(timezone.utc)
        assert before <= observation.recorded_at <= after

    def test_observation_can_be_retrieved(self, service, repository):
        observation = service.capture(_request())
        fetched = repository.get(observation.id)
        assert fetched == observation

    def test_multiple_observations_preserved_in_chronological_order(self, service, repository):
        service.capture(_request(subject="NVIDIA"))
        service.capture(_request(subject="US interest rates"))
        service.capture(_request(subject="My portfolio liquidity"))

        recorded_ats = [o.recorded_at for o in repository.list_all()]
        assert recorded_ats == sorted(recorded_ats)
        subjects = [o.subject.value for o in repository.list_all()]
        assert subjects == ["NVIDIA", "US interest rates", "My portfolio liquidity"]

    def test_same_statement_in_different_cases_is_permitted(self, service):
        first = service.capture(_request(case_id=uuid.uuid4(), statement="Repeated claim"))
        second = service.capture(_request(case_id=uuid.uuid4(), statement="Repeated claim"))
        assert first.case_id != second.case_id
        assert first.id != second.id

    def test_duplicate_statement_in_one_case_is_permitted(self, service):
        case_id = uuid.uuid4()
        first = service.capture(_request(case_id=case_id, statement="Repeated claim"))
        second = service.capture(_request(case_id=case_id, statement="Repeated claim"))
        assert first.case_id == second.case_id
        assert first.id != second.id


class TestServiceDependencySimplification:
    def test_service_depends_only_on_its_own_repository(self):
        import inspect

        signature = inspect.signature(CaptureObservationService.__init__)
        assert list(signature.parameters) == ["self", "repository"]
