"""Application-layer tests for ConclusionService (ATLAS-001 Core Loop).

Exercises the service against real (in-memory) SQLite repositories for
both Evidence and Conclusion — not fakes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.conclusion.capture_conclusion import (
    CaptureConclusionRequest,
    ConclusionService,
)
from atlas.core.domain.conclusion.exceptions import ConclusionNotFoundError
from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.conclusion.sqlalchemy_repository import (
    SqlAlchemyConclusionRepository,
)
from atlas.core.infrastructure.persistence.conclusion.table import create_conclusion_table
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table

_OBSERVED_AT = datetime(2026, 7, 13, 9, 15, 0, tzinfo=timezone.utc)
_CONCLUDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_evidence_table(eng)
    create_conclusion_table(eng)
    return eng


@pytest.fixture
def evidence_repository(engine):
    return SqlAlchemyEvidenceRepository(engine)


@pytest.fixture
def service(engine, evidence_repository):
    return ConclusionService(evidence_repository, SqlAlchemyConclusionRepository(engine))


@pytest.fixture
def existing_evidence(evidence_repository):
    evidence = Evidence.capture(
        observation_id=ObservationId(),
        statement=Statement("Order intake increased by 24 percent."),
        direction=Direction.SUPPORTS,
        observed_at=_OBSERVED_AT,
    )
    evidence_repository.add(evidence)
    return evidence


def _request(evidence_id, **overrides) -> CaptureConclusionRequest:
    defaults = dict(
        evidence_id=evidence_id.value,
        statement="The weight of evidence supports accelerating demand.",
        concluded_at=_CONCLUDED_AT,
        note="Revisit if margins compress next quarter.",
    )
    defaults.update(overrides)
    return CaptureConclusionRequest(**defaults)


class TestCapture:
    def test_captures_a_conclusion_from_existing_evidence(self, service, existing_evidence):
        conclusion = service.capture(_request(existing_evidence.id))
        assert conclusion.evidence_id == existing_evidence.id

    def test_recorded_at_is_assigned_by_atlas(self, service, existing_evidence):
        before = datetime.now(timezone.utc)
        conclusion = service.capture(_request(existing_evidence.id))
        after = datetime.now(timezone.utc)
        assert before <= conclusion.recorded_at <= after

    def test_rejects_unknown_evidence(self, service):
        with pytest.raises(EvidenceNotFoundError):
            service.capture(_request(EvidenceId()))

    def test_does_not_write_to_evidence_repository(
        self, service, evidence_repository, existing_evidence
    ):
        before = evidence_repository.list_all()
        service.capture(_request(existing_evidence.id))
        after = evidence_repository.list_all()
        assert before == after


class TestRetrieveById:
    def test_returns_the_captured_conclusion(self, service, existing_evidence):
        captured = service.capture(_request(existing_evidence.id))
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_conclusion_is_rejected(self, service):
        with pytest.raises(ConclusionNotFoundError):
            service.get(ConclusionId())


class TestRetrieveAll:
    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
