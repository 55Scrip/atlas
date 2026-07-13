"""Aggregate persistence tests for Evaluation: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.value_objects import EvaluationId, Statement
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.infrastructure.persistence.evaluation.sqlalchemy_repository import (
    SqlAlchemyEvaluationRepository,
)
from atlas.core.infrastructure.persistence.evaluation.table import create_evaluation_table

_OUTCOME_ID = OutcomeId()
_EVALUATED_AT = datetime(2026, 10, 15, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_evaluation_table(engine)
    return SqlAlchemyEvaluationRepository(engine)


def _new_evaluation(**overrides) -> Evaluation:
    defaults = dict(
        outcome_id=_OUTCOME_ID,
        statement=Statement("The decision proved correct; demand did accelerate."),
        evaluated_at=_EVALUATED_AT,
        note="Consistent with the original thesis.",
    )
    defaults.update(overrides)
    return Evaluation.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_evaluation())

    def test_persisted_evaluation_is_readable_by_id(self, repository):
        evaluation = _new_evaluation()
        repository.add(evaluation)
        assert repository.get(evaluation.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(EvaluationId()) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_evaluation(self, repository):
        first = _new_evaluation()
        second = _new_evaluation()
        repository.add(first)
        repository.add(second)
        ids = {e.id for e in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_by_outcome_id_filters_correctly(self, repository):
        other_outcome_id = OutcomeId()
        matching = _new_evaluation(outcome_id=_OUTCOME_ID)
        other = _new_evaluation(outcome_id=other_outcome_id)
        repository.add(matching)
        repository.add(other)

        result = repository.list_by_outcome_id(_OUTCOME_ID)

        assert [e.id for e in result] == [matching.id]

    def test_list_all_is_chronological_by_evaluated_at_ascending(self, repository):
        evaluated_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for evaluated_at in evaluated_ats:
            repository.add(_new_evaluation(evaluated_at=evaluated_at))

        result = [e.evaluated_at for e in repository.list_all()]
        assert result == sorted(evaluated_ats)


class TestEqualsOriginal:
    def test_round_tripped_evaluation_equals_the_original_in_every_field(self, repository):
        original = _new_evaluation()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.outcome_id == original.outcome_id
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.evaluated_at == original.evaluated_at
        assert reloaded.recorded_at == original.recorded_at

    def test_evaluated_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_evaluation()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.evaluated_at.utcoffset() == timedelta(hours=2)
        assert reloaded.evaluated_at.isoformat() == "2026-10-15T09:00:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_evaluation_table_has_no_sql_foreign_key(self, repository):
        from atlas.core.infrastructure.persistence.evaluation.table import evaluations_table

        column_names = set(evaluations_table.columns.keys())
        assert column_names == {
            "evaluation_id",
            "outcome_id",
            "statement",
            "note",
            "evaluated_at",
            "recorded_at",
        }
        assert evaluations_table.foreign_keys == set()
