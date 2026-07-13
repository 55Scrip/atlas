"""Aggregate persistence tests for Question: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.question.entity import Question
from atlas.core.domain.question.value_objects import QuestionId, Statement
from atlas.core.infrastructure.persistence.question.sqlalchemy_repository import (
    SqlAlchemyQuestionRepository,
)
from atlas.core.infrastructure.persistence.question.table import create_question_table

_RAISED_AT = datetime(2026, 7, 13, 8, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_question_table(engine)
    return SqlAlchemyQuestionRepository(engine)


def _new_question(**overrides) -> Question:
    defaults = dict(
        statement=Statement("Is demand for AI infrastructure accelerating?"),
        raised_at=_RAISED_AT,
        note="Prompted by the earnings call.",
    )
    defaults.update(overrides)
    return Question.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_question())

    def test_persisted_question_is_readable_by_id(self, repository):
        question = _new_question()
        repository.add(question)
        assert repository.get(question.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(QuestionId()) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_question(self, repository):
        first = _new_question()
        second = _new_question()
        repository.add(first)
        repository.add(second)
        ids = {q.id for q in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_all_is_chronological_by_raised_at_ascending(self, repository):
        raised_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for raised_at in raised_ats:
            repository.add(_new_question(raised_at=raised_at))

        result = [q.raised_at for q in repository.list_all()]
        assert result == sorted(raised_ats)


class TestEqualsOriginal:
    def test_round_tripped_question_equals_the_original_in_every_field(self, repository):
        original = _new_question()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.raised_at == original.raised_at
        assert reloaded.recorded_at == original.recorded_at

    def test_optional_note_round_trips_as_none(self, repository):
        original = _new_question(note=None)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.note is None

    def test_raised_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_question()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.raised_at.utcoffset() == timedelta(hours=2)
        assert reloaded.raised_at.isoformat() == "2026-07-13T08:00:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_question_table_has_no_columns_referencing_another_aggregate(self, repository):
        from atlas.core.infrastructure.persistence.question.table import questions_table

        column_names = set(questions_table.columns.keys())
        assert column_names == {"question_id", "statement", "note", "raised_at", "recorded_at"}
        assert questions_table.foreign_keys == set()
