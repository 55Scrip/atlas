"""Aggregate persistence tests for Learning: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.learning.value_objects import LearningId, Statement
from atlas.core.infrastructure.persistence.learning.sqlalchemy_repository import (
    SqlAlchemyLearningRepository,
)
from atlas.core.infrastructure.persistence.learning.table import create_learning_table

_EVALUATION_ID = EvaluationId()
_LEARNED_AT = datetime(2026, 10, 16, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_learning_table(engine)
    return SqlAlchemyLearningRepository(engine)


def _new_learning(**overrides) -> Learning:
    defaults = dict(
        evaluation_id=_EVALUATION_ID,
        statement=Statement("Weigh capex guidance more heavily than headline revenue growth."),
        learned_at=_LEARNED_AT,
        note="Apply this to the next earnings cycle.",
    )
    defaults.update(overrides)
    return Learning.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_learning())

    def test_persisted_learning_is_readable_by_id(self, repository):
        learning = _new_learning()
        repository.add(learning)
        assert repository.get(learning.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(LearningId()) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_learning(self, repository):
        first = _new_learning()
        second = _new_learning()
        repository.add(first)
        repository.add(second)
        ids = {learning.id for learning in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_by_evaluation_id_filters_correctly(self, repository):
        other_evaluation_id = EvaluationId()
        matching = _new_learning(evaluation_id=_EVALUATION_ID)
        other = _new_learning(evaluation_id=other_evaluation_id)
        repository.add(matching)
        repository.add(other)

        result = repository.list_by_evaluation_id(_EVALUATION_ID)

        assert [learning.id for learning in result] == [matching.id]

    def test_list_all_is_chronological_by_learned_at_ascending(self, repository):
        learned_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for learned_at in learned_ats:
            repository.add(_new_learning(learned_at=learned_at))

        result = [learning.learned_at for learning in repository.list_all()]
        assert result == sorted(learned_ats)


class TestEqualsOriginal:
    def test_round_tripped_learning_equals_the_original_in_every_field(self, repository):
        original = _new_learning()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.evaluation_id == original.evaluation_id
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.learned_at == original.learned_at
        assert reloaded.recorded_at == original.recorded_at

    def test_learned_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_learning()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.learned_at.utcoffset() == timedelta(hours=2)
        assert reloaded.learned_at.isoformat() == "2026-10-16T09:00:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_learning_table_has_no_sql_foreign_key(self, repository):
        from atlas.core.infrastructure.persistence.learning.table import learnings_table

        column_names = set(learnings_table.columns.keys())
        assert column_names == {
            "learning_id",
            "evaluation_id",
            "statement",
            "note",
            "learned_at",
            "recorded_at",
        }
        assert learnings_table.foreign_keys == set()
