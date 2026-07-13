"""Application-layer tests for QuestionService (ATLAS-001 Core Loop)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.application.question.capture_question import (
    CaptureQuestionRequest,
    QuestionService,
)
from atlas.core.domain.question.exceptions import QuestionNotFoundError
from atlas.core.domain.question.value_objects import QuestionId
from atlas.core.infrastructure.persistence.question.sqlalchemy_repository import (
    SqlAlchemyQuestionRepository,
)
from atlas.core.infrastructure.persistence.question.table import create_question_table

_RAISED_AT = datetime(2026, 7, 13, 8, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def service():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_question_table(engine)
    return QuestionService(SqlAlchemyQuestionRepository(engine))


def _request(**overrides) -> CaptureQuestionRequest:
    defaults = dict(
        statement="Is demand for AI infrastructure accelerating?",
        raised_at=_RAISED_AT,
        note="Prompted by the earnings call.",
    )
    defaults.update(overrides)
    return CaptureQuestionRequest(**defaults)


class TestCapture:
    def test_captures_a_question(self, service):
        question = service.capture(_request())
        assert question.statement.value == "Is demand for AI infrastructure accelerating?"

    def test_recorded_at_is_assigned_by_atlas(self, service):
        before = datetime.now(timezone.utc)
        question = service.capture(_request())
        after = datetime.now(timezone.utc)
        assert before <= question.recorded_at <= after


class TestRetrieveById:
    def test_returns_the_captured_question(self, service):
        captured = service.capture(_request())
        retrieved = service.get(captured.id)
        assert retrieved == captured

    def test_unknown_question_is_rejected(self, service):
        with pytest.raises(QuestionNotFoundError):
            service.get(QuestionId())


class TestRetrieveAll:
    def test_empty_when_nothing_captured(self, service):
        assert service.list_all() == []

    def test_multiple_questions_are_returned_in_chronological_order(self, service):
        service.capture(_request(raised_at=datetime(2026, 1, 3, tzinfo=timezone.utc)))
        service.capture(_request(raised_at=datetime(2026, 1, 1, tzinfo=timezone.utc)))
        service.capture(_request(raised_at=datetime(2026, 1, 2, tzinfo=timezone.utc)))

        result = [q.raised_at for q in service.list_all()]
        assert result == sorted(result)
