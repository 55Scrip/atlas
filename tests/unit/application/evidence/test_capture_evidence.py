"""Application-layer tests for EvidenceService (API-005).

Exercises the service against real (in-memory) SQLite repositories for
both Observation and Evidence — not fakes — since the behavior under
test (does the referenced Observation exist?) is precisely the
interaction between the two real repositories, the same convention
`test_capture_decision_context.py` already established for the
identical shape of cross-aggregate check.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.evidence.capture_evidence import (
    CaptureEvidenceRequest,
    EvidenceService,
    ObservationNotFoundError,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import ObservationId, Statement, Subject
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table

_OBSERVED_AT = datetime(2026, 7, 13, 9, 15, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_observation_table(eng)
    create_evidence_table(eng)
    return eng


@pytest.fixture
def observation_repository(engine):
    return SqlAlchemyObservationRepository(engine)


@pytest.fixture
def service(engine, observation_repository):
    return EvidenceService(observation_repository, SqlAlchemyEvidenceRepository(engine))


@pytest.fixture
def existing_observation_id(observation_repository) -> ObservationId:
    observation = Observation.capture(
        case_id=CaseId(),
        subject=Subject("Semiconductor sector"),
        statement=Statement("Revenue increased by 18 percent."),
        observed_at=_OBSERVED_AT,
    )
    observation_repository.add(observation)
    return observation.id


def _request(observation_id: ObservationId, **overrides) -> CaptureEvidenceRequest:
    defaults = dict(
        observation_id=observation_id.value,
        statement=(
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        ),
        direction="SUPPORTS",
        observed_at=_OBSERVED_AT,
        source="Quarterly earnings report",
        note="The comparison benefits from a weak prior-year period.",
    )
    defaults.update(overrides)
    return CaptureEvidenceRequest(**defaults)


class TestCapture:
    def test_captures_evidence(self, service, existing_observation_id):
        evidence = service.capture(_request(existing_observation_id))
        assert evidence.observation_id == existing_observation_id
        assert evidence.statement.value == (
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        )
        assert evidence.direction.value == "SUPPORTS"

    def test_recorded_at_is_assigned_by_atlas(self, service, existing_observation_id):
        before = datetime.now(timezone.utc)
        evidence = service.capture(_request(existing_observation_id))
        after = datetime.now(timezone.utc)
        assert before <= evidence.recorded_at <= after

    def test_rejects_a_nonexistent_observation(self, service):
        with pytest.raises(ObservationNotFoundError):
            service.capture(_request(ObservationId()))

    def test_does_not_write_to_the_observation_repository(
        self, service, observation_repository, existing_observation_id
    ):
        before = observation_repository.get(existing_observation_id)
        service.capture(_request(existing_observation_id))
        after = observation_repository.get(existing_observation_id)
        assert before == after


class TestRetrieveById:
    def test_returns_the_captured_evidence(self, service, existing_observation_id):
        captured = service.capture(_request(existing_observation_id))
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_evidence_is_rejected(self, service):
        with pytest.raises(EvidenceNotFoundError):
            service.get(EvidenceId())


class TestRetrieveAll:
    def test_multiple_evidence_records_are_returned_in_chronological_order(
        self, service, existing_observation_id
    ):
        service.capture(
            _request(existing_observation_id, observed_at=datetime(2026, 1, 3, tzinfo=timezone.utc))
        )
        service.capture(
            _request(existing_observation_id, observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        )
        service.capture(
            _request(existing_observation_id, observed_at=datetime(2026, 1, 2, tzinfo=timezone.utc))
        )

        result = [e.observed_at for e in service.list_all()]
        assert result == sorted(result)

    def test_mixed_utc_offsets_sort_by_true_absolute_instant(
        self, service, existing_observation_id
    ):
        later_but_higher_offset = datetime(2026, 3, 1, 10, 0, tzinfo=timezone(timedelta(hours=5)))
        earlier_but_lower_offset = datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc)
        assert later_but_higher_offset < earlier_but_lower_offset  # sanity check on the fixture

        service.capture(_request(existing_observation_id, observed_at=later_but_higher_offset))
        service.capture(_request(existing_observation_id, observed_at=earlier_but_lower_offset))

        result = [e.observed_at for e in service.list_all()]
        assert result == [later_but_higher_offset, earlier_but_lower_offset]

    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []


class TestDelete:
    def test_deletes_existing_evidence(self, service, existing_observation_id):
        evidence = service.capture(_request(existing_observation_id))
        service.delete(evidence.id)
        with pytest.raises(EvidenceNotFoundError):
            service.get(evidence.id)

    def test_deleted_evidence_is_absent_from_list_all(self, service, existing_observation_id):
        evidence = service.capture(_request(existing_observation_id))
        service.delete(evidence.id)
        assert evidence.id not in [e.id for e in service.list_all()]

    def test_deleting_an_unknown_id_is_rejected(self, service):
        with pytest.raises(EvidenceNotFoundError):
            service.delete(EvidenceId())
