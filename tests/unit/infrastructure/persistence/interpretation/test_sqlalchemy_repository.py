"""Aggregate persistence tests for Interpretation: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.interpretation.entity import Interpretation
from atlas.core.domain.interpretation.value_objects import InterpretationId, Statement
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.interpretation.sqlalchemy_repository import (
    SqlAlchemyInterpretationRepository,
)
from atlas.core.infrastructure.persistence.interpretation.table import (
    create_interpretation_table,
)

_OBSERVATION_ID = ObservationId()
_INTERPRETED_AT = datetime(2026, 7, 13, 9, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_interpretation_table(engine)
    return SqlAlchemyInterpretationRepository(engine)


def _new_interpretation(**overrides) -> Interpretation:
    defaults = dict(
        observation_id=_OBSERVATION_ID,
        statement=Statement("This suggests demand may be accelerating."),
        interpreted_at=_INTERPRETED_AT,
        note="Worth revisiting after the next report.",
    )
    defaults.update(overrides)
    return Interpretation.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_interpretation())

    def test_persisted_interpretation_is_readable_by_id(self, repository):
        interpretation = _new_interpretation()
        repository.add(interpretation)
        assert repository.get(interpretation.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(InterpretationId()) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_interpretation(self, repository):
        first = _new_interpretation()
        second = _new_interpretation()
        repository.add(first)
        repository.add(second)
        ids = {i.id for i in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_by_observation_id_filters_correctly(self, repository):
        other_observation_id = ObservationId()
        matching = _new_interpretation(observation_id=_OBSERVATION_ID)
        other = _new_interpretation(observation_id=other_observation_id)
        repository.add(matching)
        repository.add(other)

        result = repository.list_by_observation_id(_OBSERVATION_ID)

        assert [i.id for i in result] == [matching.id]

    def test_list_all_is_chronological_by_interpreted_at_ascending(self, repository):
        interpreted_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for interpreted_at in interpreted_ats:
            repository.add(_new_interpretation(interpreted_at=interpreted_at))

        result = [i.interpreted_at for i in repository.list_all()]
        assert result == sorted(interpreted_ats)


class TestEqualsOriginal:
    def test_round_tripped_interpretation_equals_the_original_in_every_field(self, repository):
        original = _new_interpretation()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.observation_id == original.observation_id
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.interpreted_at == original.interpreted_at
        assert reloaded.recorded_at == original.recorded_at

    def test_interpreted_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_interpretation()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.interpreted_at.utcoffset() == timedelta(hours=2)
        assert reloaded.interpreted_at.isoformat() == "2026-07-13T09:00:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_interpretation_table_has_no_sql_foreign_key(self, repository):
        from atlas.core.infrastructure.persistence.interpretation.table import (
            interpretations_table,
        )

        column_names = set(interpretations_table.columns.keys())
        assert column_names == {
            "interpretation_id",
            "observation_id",
            "statement",
            "note",
            "interpreted_at",
            "recorded_at",
        }
        assert interpretations_table.foreign_keys == set()
