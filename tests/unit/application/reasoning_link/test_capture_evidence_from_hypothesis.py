"""Tests for CaptureEvidenceFromHypothesisService (ATLAS-001 Core Loop, step 5 of 10)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.evidence.capture_evidence import EvidenceService
from atlas.core.application.reasoning_link.capture_evidence_from_hypothesis import (
    CaptureEvidenceFromHypothesisRequest,
    CaptureEvidenceFromHypothesisService,
)
from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.hypothesis.exceptions import HypothesisNotFoundError
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.domain.hypothesis.value_objects import Statement as HypothesisStatement
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyHypothesisEvidenceLinkRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    create_reasoning_link_tables,
)

_FORMULATED_AT = datetime(2026, 7, 13, 10, 0, 0, tzinfo=timezone.utc)
_OBSERVED_AT = datetime(2026, 7, 13, 9, 15, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_hypothesis_table(eng)
    create_evidence_table(eng)
    create_reasoning_link_tables(eng)
    return eng


@pytest.fixture
def hypothesis_repository(engine):
    return SqlAlchemyHypothesisRepository(engine)


@pytest.fixture
def link_repository(engine):
    return SqlAlchemyHypothesisEvidenceLinkRepository(engine)


@pytest.fixture
def service(engine, hypothesis_repository, link_repository):
    evidence_service = EvidenceService(SqlAlchemyEvidenceRepository(engine))
    return CaptureEvidenceFromHypothesisService(
        hypothesis_repository, evidence_service, link_repository
    )


@pytest.fixture
def existing_hypothesis(hypothesis_repository):
    hypothesis = Hypothesis.capture(
        statement=HypothesisStatement("Demand for AI infrastructure may be accelerating."),
        formulated_at=_FORMULATED_AT,
    )
    hypothesis_repository.add(hypothesis)
    return hypothesis


def _request(hypothesis_id, **overrides) -> CaptureEvidenceFromHypothesisRequest:
    defaults = dict(
        hypothesis_id=hypothesis_id.value,
        statement="Order intake increased by 24 percent.",
        direction="SUPPORTS",
        observed_at=_OBSERVED_AT,
    )
    defaults.update(overrides)
    return CaptureEvidenceFromHypothesisRequest(**defaults)


class TestCaptureEvidenceFromHypothesis:
    def test_creates_evidence_and_a_link(self, service, existing_hypothesis):
        result = service.capture(_request(existing_hypothesis.id))
        assert result.evidence.statement.value == "Order intake increased by 24 percent."
        assert result.evidence.direction.value == "SUPPORTS"
        assert result.link.hypothesis_id == existing_hypothesis.id
        assert result.link.evidence_id == result.evidence.id

    def test_rejects_unknown_hypothesis(self, service):
        with pytest.raises(HypothesisNotFoundError):
            service.capture(_request(HypothesisId()))

    def test_does_not_write_to_hypothesis_repository(
        self, service, hypothesis_repository, existing_hypothesis
    ):
        before = hypothesis_repository.list_all()
        service.capture(_request(existing_hypothesis.id))
        after = hypothesis_repository.list_all()
        assert before == after

    def test_link_is_persisted_and_queryable(
        self, service, link_repository, existing_hypothesis
    ):
        result = service.capture(_request(existing_hypothesis.id))
        links = link_repository.list_by_hypothesis_id(existing_hypothesis.id)
        assert [link.link_id for link in links] == [result.link.link_id]
