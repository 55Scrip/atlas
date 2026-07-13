"""Application-layer tests for EvidenceService (API-005).

Exercises the service against a real (in-memory) SQLite repository, not a
fake, for genuine round-trip behavior — matching the convention used
elsewhere in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.evidence.capture_evidence import (
    CaptureEvidenceRequest,
    EvidenceService,
)
from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table

_OBSERVED_AT = datetime(2026, 7, 13, 9, 15, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def service():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_evidence_table(engine)
    return EvidenceService(SqlAlchemyEvidenceRepository(engine))


def _request(**overrides) -> CaptureEvidenceRequest:
    defaults = dict(
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
    def test_captures_evidence(self, service):
        evidence = service.capture(_request())
        assert evidence.statement.value == (
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        )
        assert evidence.direction.value == "SUPPORTS"

    def test_recorded_at_is_assigned_by_atlas(self, service):
        before = datetime.now(timezone.utc)
        evidence = service.capture(_request())
        after = datetime.now(timezone.utc)
        assert before <= evidence.recorded_at <= after


class TestRetrieveById:
    def test_returns_the_captured_evidence(self, service):
        captured = service.capture(_request())
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_evidence_is_rejected(self, service):
        with pytest.raises(EvidenceNotFoundError):
            service.get(EvidenceId())


class TestRetrieveAll:
    def test_multiple_evidence_records_are_returned_in_chronological_order(self, service):
        service.capture(_request(observed_at=datetime(2026, 1, 3, tzinfo=timezone.utc)))
        service.capture(_request(observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
        service.capture(_request(observed_at=datetime(2026, 1, 2, tzinfo=timezone.utc)))

        result = [e.observed_at for e in service.list_all()]
        assert result == sorted(result)

    def test_mixed_utc_offsets_sort_by_true_absolute_instant(self, service):
        later_but_higher_offset = datetime(2026, 3, 1, 10, 0, tzinfo=timezone(timedelta(hours=5)))
        earlier_but_lower_offset = datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc)
        assert later_but_higher_offset < earlier_but_lower_offset  # sanity check on the fixture

        service.capture(_request(observed_at=later_but_higher_offset))
        service.capture(_request(observed_at=earlier_but_lower_offset))

        result = [e.observed_at for e in service.list_all()]
        assert result == [later_but_higher_offset, earlier_but_lower_offset]

    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
