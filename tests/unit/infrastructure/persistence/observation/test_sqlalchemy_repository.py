"""Aggregate persistence tests for Observation: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import ObservationId, Statement, Subject
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table

_OBSERVED_AT = datetime(2026, 7, 13, 10, 30, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_observation_table(engine)
    return SqlAlchemyObservationRepository(engine)


def _new_observation(**overrides) -> Observation:
    defaults = dict(
        case_id=CaseId(),
        subject=Subject("Semiconductor sector"),
        statement=Statement(
            "Several semiconductor companies raised capital expenditure "
            "guidance during the same reporting period."
        ),
        observed_at=_OBSERVED_AT,
        source="Quarterly earnings reports",
        note="Follow whether equipment suppliers report the same pattern.",
    )
    defaults.update(overrides)
    return Observation.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_observation())

    def test_persisted_observation_is_readable_by_id(self, repository):
        observation = _new_observation()
        repository.add(observation)
        assert repository.get(observation.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        unknown = ObservationId()
        assert repository.get(unknown) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_observation(self, repository):
        first = _new_observation()
        second = _new_observation()
        repository.add(first)
        repository.add(second)
        ids = {o.id for o in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_all_is_chronological_by_recorded_at(self, repository):
        clocks = [
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
            datetime(2026, 1, 3, tzinfo=timezone.utc),
        ]
        for clock_time in reversed(clocks):
            # insert out of chronological order to prove ordering is by
            # recorded_at, not insertion order
            repository.add(_new_observation(clock=(lambda dt=clock_time: dt)))

        recorded_ats = [o.recorded_at for o in repository.list_all()]
        assert recorded_ats == sorted(recorded_ats)


class TestEqualsOriginal:
    def test_round_tripped_observation_equals_the_original_in_every_field(self, repository):
        original = _new_observation()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.case_id == original.case_id
        assert reloaded.subject == original.subject
        assert reloaded.statement == original.statement
        assert reloaded.source == original.source
        assert reloaded.note == original.note
        assert reloaded.observed_at == original.observed_at
        assert reloaded.recorded_at == original.recorded_at

    def test_optional_fields_round_trip_as_none(self, repository):
        original = _new_observation(source=None, note=None)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.source is None
        assert reloaded.note is None

    def test_observed_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_observation()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.observed_at.utcoffset() == timedelta(hours=2)
        assert reloaded.observed_at.isoformat() == "2026-07-13T10:30:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestCaseOwnership:
    def test_same_statement_in_different_cases_is_permitted(self, repository):
        first = _new_observation(statement=Statement("Repeated claim"))
        second = _new_observation(statement=Statement("Repeated claim"))
        repository.add(first)
        repository.add(second)
        assert first.case_id != second.case_id
        assert repository.get(first.id).statement == repository.get(second.id).statement

    def test_duplicate_statement_in_one_case_is_permitted(self, repository):
        case_id = CaseId()
        first = _new_observation(case_id=case_id, statement=Statement("Repeated claim"))
        second = _new_observation(case_id=case_id, statement=Statement("Repeated claim"))
        repository.add(first)
        repository.add(second)
        assert repository.get(first.id).case_id == repository.get(second.id).case_id
        assert first.id != second.id

    def test_case_id_not_null_is_enforced(self, repository):
        engine = repository._engine
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                from atlas.core.infrastructure.persistence.observation.table import (
                    observations_table,
                )

                connection.execute(
                    insert(observations_table).values(
                        observation_id=str(ObservationId()),
                        case_id=None,
                        subject="Semiconductor sector",
                        statement="Something happened.",
                        source=None,
                        note=None,
                        observed_at=_OBSERVED_AT.isoformat(),
                        recorded_at=_OBSERVED_AT.isoformat(),
                    )
                )


class TestNoForeignKeysOrCoupling:
    def test_observation_table_has_no_decision_or_context_columns(self, repository):
        # A structural check that the table stays standalone: only the
        # columns API-003 (as corrected for Case ownership) defines,
        # nothing referencing another aggregate.
        from atlas.core.infrastructure.persistence.observation.table import observations_table

        column_names = set(observations_table.columns.keys())
        assert column_names == {
            "observation_id",
            "case_id",
            "subject",
            "statement",
            "source",
            "note",
            "observed_at",
            "recorded_at",
        }

    def test_no_foreign_key_to_any_other_table(self, repository):
        from atlas.core.infrastructure.persistence.observation.table import observations_table

        assert observations_table.foreign_keys == set()
