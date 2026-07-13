"""Application-layer tests for HypothesisService (API-004).

Exercises the service against a real (in-memory) SQLite repository, not a
fake, for genuine round-trip behavior — matching the convention used
elsewhere in this codebase.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.hypothesis.capture_hypothesis import (
    CaptureHypothesisRequest,
    HypothesisService,
)
from atlas.core.domain.hypothesis.exceptions import HypothesisNotFoundError
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table

_FORMULATED_AT = datetime(2026, 7, 13, 18, 30, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def service():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_hypothesis_table(engine)
    return HypothesisService(SqlAlchemyHypothesisRepository(engine))


def _request(**overrides) -> CaptureHypothesisRequest:
    defaults = dict(
        statement=(
            "Demand for AI infrastructure may be accelerating faster than "
            "the market expects."
        ),
        formulated_at=_FORMULATED_AT,
        note="Revisit after the next reporting cycle.",
    )
    defaults.update(overrides)
    return CaptureHypothesisRequest(**defaults)


class TestCapture:
    def test_captures_a_hypothesis(self, service):
        hypothesis = service.capture(_request())
        assert hypothesis.statement.value == (
            "Demand for AI infrastructure may be accelerating faster than "
            "the market expects."
        )

    def test_recorded_at_is_assigned_by_atlas(self, service):
        before = datetime.now(timezone.utc)
        hypothesis = service.capture(_request())
        after = datetime.now(timezone.utc)
        assert before <= hypothesis.recorded_at <= after


class TestRetrieveById:
    def test_returns_the_captured_hypothesis(self, service):
        captured = service.capture(_request())
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_hypothesis_is_rejected(self, service):
        with pytest.raises(HypothesisNotFoundError):
            service.get(HypothesisId())


class TestRetrieveAll:
    def test_multiple_hypotheses_are_returned_in_chronological_order(self, service):
        service.capture(_request(formulated_at=datetime(2026, 1, 3, tzinfo=timezone.utc)))
        service.capture(_request(formulated_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
        service.capture(_request(formulated_at=datetime(2026, 1, 2, tzinfo=timezone.utc)))

        result = [h.formulated_at for h in service.list_all()]
        assert result == sorted(result)

    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []
