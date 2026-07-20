"""Tests for ObserveFromQuestionService (ATLAS-001 Core Loop, step 2 of 10)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.observation.capture_observation import CaptureObservationService
from atlas.core.application.reasoning_link.observe_from_question import (
    ObserveFromQuestionRequest,
    ObserveFromQuestionService,
)
from atlas.core.domain.question.entity import Question
from atlas.core.domain.question.exceptions import QuestionNotFoundError
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.domain.question.value_objects import Statement as QuestionStatement
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table
from atlas.core.infrastructure.persistence.question.sqlalchemy_repository import (
    SqlAlchemyQuestionRepository,
)
from atlas.core.infrastructure.persistence.question.table import create_question_table
from atlas.core.infrastructure.persistence.reasoning_link.sqlalchemy_repository import (
    SqlAlchemyQuestionObservationLinkRepository,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    create_reasoning_link_tables,
)

_RAISED_AT = datetime(2026, 7, 13, 8, 0, 0, tzinfo=timezone.utc)
_OBSERVED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_question_table(eng)
    create_observation_table(eng)
    create_reasoning_link_tables(eng)
    return eng


@pytest.fixture
def question_repository(engine):
    return SqlAlchemyQuestionRepository(engine)


@pytest.fixture
def link_repository(engine):
    return SqlAlchemyQuestionObservationLinkRepository(engine)


@pytest.fixture
def service(engine, question_repository, link_repository):
    observation_service = CaptureObservationService(SqlAlchemyObservationRepository(engine))
    return ObserveFromQuestionService(question_repository, observation_service, link_repository)


@pytest.fixture
def existing_question(question_repository):
    question = Question.capture(
        statement=QuestionStatement("Is demand for AI infrastructure accelerating?"),
        raised_at=_RAISED_AT,
    )
    question_repository.add(question)
    return question


def _request(question_id, **overrides) -> ObserveFromQuestionRequest:
    defaults = dict(
        case_id=uuid.uuid4(),
        question_id=question_id.value,
        subject="Semiconductor sector",
        statement="Several companies raised capex guidance.",
        observed_at=_OBSERVED_AT,
    )
    defaults.update(overrides)
    return ObserveFromQuestionRequest(**defaults)


class TestObserveFromQuestion:
    def test_creates_an_observation_and_a_link(self, service, existing_question):
        result = service.observe(_request(existing_question.id))
        assert result.observation.statement.value == "Several companies raised capex guidance."
        assert result.link.question_id == existing_question.id
        assert result.link.observation_id == result.observation.id

    def test_propagates_exactly_the_requests_case_id_unchanged(
        self, service, existing_question
    ):
        request = _request(existing_question.id)
        result = service.observe(request)
        assert result.observation.case_id.value == request.case_id

    def test_rejects_unknown_question(self, service):
        with pytest.raises(QuestionNotFoundError):
            service.observe(_request(QuestionId()))

    def test_does_not_write_to_question_repository(
        self, service, question_repository, existing_question
    ):
        before = question_repository.list_all()
        service.observe(_request(existing_question.id))
        after = question_repository.list_all()
        assert before == after

    def test_link_is_persisted_and_queryable(self, service, link_repository, existing_question):
        result = service.observe(_request(existing_question.id))
        links = link_repository.list_by_question_id(existing_question.id)
        assert [link.link_id for link in links] == [result.link.link_id]

    def test_nothing_is_written_when_question_is_unknown(
        self, service, link_repository, engine
    ):
        with pytest.raises(QuestionNotFoundError):
            service.observe(_request(QuestionId()))
        from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
            SqlAlchemyObservationRepository,
        )

        assert SqlAlchemyObservationRepository(engine).list_all() == []
