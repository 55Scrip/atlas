"""Application-layer tests for InterpretationService (ATLAS-001 Core Loop).

Exercises the service against real (in-memory) SQLite repositories for
both Observation and Interpretation — not fakes — since the behavior
under test (does the referenced Observation exist?) is precisely the
interaction between the two real repositories.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.interpretation.capture_interpretation import (
    CaptureInterpretationRequest,
    InterpretationService,
    ObservationNotFoundError,
)
from atlas.core.domain.interpretation.exceptions import InterpretationNotFoundError
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import Statement, Subject
from atlas.core.infrastructure.persistence.interpretation.sqlalchemy_repository import (
    SqlAlchemyInterpretationRepository,
)
from atlas.core.infrastructure.persistence.interpretation.table import (
    create_interpretation_table,
)
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table

_OBSERVED_AT = datetime(2026, 7, 13, 8, 30, 0, tzinfo=timezone.utc)
_INTERPRETED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_observation_table(eng)
    create_interpretation_table(eng)
    return eng


@pytest.fixture
def observation_repository(engine):
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def service(engine, observation_repository):
    return InterpretationService(
        observation_repository, SqlAlchemyInterpretationRepository(engine)
    )


@pytest.fixture
def existing_observation(observation_repository):
    observation = Observation.capture(
        subject=Subject("Semiconductor sector"),
        statement=Statement("Several companies raised capex guidance."),
        observed_at=_OBSERVED_AT,
    )
    observation_repository.add(observation)
    return observation


def _request(observation_id, **overrides) -> CaptureInterpretationRequest:
    defaults = dict(
        observation_id=observation_id.value,
        statement="This suggests demand may be accelerating.",
        interpreted_at=_INTERPRETED_AT,
        note="Worth revisiting after the next report.",
    )
    defaults.update(overrides)
    return CaptureInterpretationRequest(**defaults)


class TestCapture:
    def test_captures_an_interpretation_of_an_existing_observation(
        self, service, existing_observation
    ):
        interpretation = service.capture(_request(existing_observation.id))
        assert interpretation.observation_id == existing_observation.id

    def test_recorded_at_is_assigned_by_atlas(self, service, existing_observation):
        before = datetime.now(timezone.utc)
        interpretation = service.capture(_request(existing_observation.id))
        after = datetime.now(timezone.utc)
        assert before <= interpretation.recorded_at <= after

    def test_rejects_unknown_observation(self, service):
        from atlas.core.domain.observation.value_objects import ObservationId

        with pytest.raises(ObservationNotFoundError):
            service.capture(_request(ObservationId()))

    def test_does_not_write_to_observation_repository(
        self, service, observation_repository, existing_observation
    ):
        before = observation_repository.list_all()
        service.capture(_request(existing_observation.id))
        after = observation_repository.list_all()
        assert before == after


class TestRetrieveById:
    def test_returns_the_captured_interpretation(self, service, existing_observation):
        captured = service.capture(_request(existing_observation.id))
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_interpretation_is_rejected(self, service):
        with pytest.raises(InterpretationNotFoundError):
            service.get(InterpretationId())


class TestRetrieveAll:
    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
