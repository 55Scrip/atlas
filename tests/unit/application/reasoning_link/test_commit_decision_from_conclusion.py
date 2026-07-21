"""Tests for CommitDecisionFromConclusionService (ATLAS-001 Core Loop, step 7 of 10)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.decision.capture_decision import CaptureDecisionService
from atlas.core.application.reasoning_link.commit_decision_from_conclusion import (
    CommitDecisionFromConclusionRequest,
    CommitDecisionFromConclusionService,
)
from atlas.core.domain.conclusion.entity import Conclusion
from atlas.core.domain.conclusion.exceptions import ConclusionNotFoundError
from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.conclusion.value_objects import Statement as ConclusionStatement
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.infrastructure.persistence.conclusion.sqlalchemy_repository import (
    SqlAlchemyConclusionRepository,
)
from atlas.core.infrastructure.persistence.conclusion.table import create_conclusion_table
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyConclusionDecisionLinkRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    create_reasoning_link_tables,
)

_CONCLUDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
_DECIDED_AT = datetime(2026, 7, 13, 13, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_conclusion_table(eng)
    create_decision_table(eng)
    create_reasoning_link_tables(eng)
    return eng


@pytest.fixture
def conclusion_repository(engine):
    return SqlAlchemyConclusionRepository(engine)


@pytest.fixture
def link_repository(engine):
    return SqlAlchemyConclusionDecisionLinkRepository(engine)


@pytest.fixture
def service(engine, conclusion_repository, link_repository):
    decision_service = CaptureDecisionService(SqlAlchemyDecisionRepository(engine))
    return CommitDecisionFromConclusionService(
        conclusion_repository, decision_service, link_repository
    )


@pytest.fixture
def existing_conclusion(conclusion_repository):
    conclusion = Conclusion.capture(
        evidence_id=EvidenceId(),
        statement=ConclusionStatement("The weight of evidence supports accelerating demand."),
        concluded_at=_CONCLUDED_AT,
    )
    conclusion_repository.add(conclusion)
    return conclusion


def _request(conclusion_id, **overrides) -> CommitDecisionFromConclusionRequest:
    defaults = dict(
        case_id=uuid.uuid4(),
        conclusion_id=conclusion_id.value,
        user_id=uuid.uuid4(),
        decision_type="BUY",
        subject="NVIDIA",
        reason="Demand for AI infrastructure is accelerating.",
        confidence=80,
        decided_at=_DECIDED_AT,
    )
    defaults.update(overrides)
    return CommitDecisionFromConclusionRequest(**defaults)


class TestCommitDecisionFromConclusion:
    def test_creates_a_decision_and_a_link(self, service, existing_conclusion):
        result = service.commit(_request(existing_conclusion.id))
        assert result.decision.subject.value == "NVIDIA"
        assert result.link.conclusion_id == existing_conclusion.id
        assert result.link.decision_id == result.decision.id

    def test_propagates_exactly_the_requests_case_id_unchanged(
        self, service, existing_conclusion
    ):
        request = _request(existing_conclusion.id)
        result = service.commit(request)
        assert result.decision.case_id.value == request.case_id

    def test_rejects_unknown_conclusion(self, service):
        with pytest.raises(ConclusionNotFoundError):
            service.commit(_request(ConclusionId()))

    def test_does_not_write_to_conclusion_repository(
        self, service, conclusion_repository, existing_conclusion
    ):
        before = conclusion_repository.list_all()
        service.commit(_request(existing_conclusion.id))
        after = conclusion_repository.list_all()
        assert before == after

    def test_link_is_persisted_and_queryable(
        self, service, link_repository, existing_conclusion
    ):
        result = service.commit(_request(existing_conclusion.id))
        links = link_repository.list_by_conclusion_id(existing_conclusion.id)
        assert [link.link_id for link in links] == [result.link.link_id]
