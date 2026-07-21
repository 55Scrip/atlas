"""Aggregate persistence tests for Outcome: create, persist, read, equals original."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import OutcomeId, Statement
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table, outcomes_table

_DECISION_ID = DecisionId()
_OCCURRED_AT = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_outcome_table(engine)
    return SqlAlchemyOutcomeRepository(engine)


def _new_outcome(**overrides) -> Outcome:
    defaults = dict(
        case_id=CaseId(),
        decision_id=_DECISION_ID,
        statement=Statement("Revenue growth accelerated as expected."),
        occurred_at=_OCCURRED_AT,
        note="Confirmed by the following quarter's report.",
    )
    defaults.update(overrides)
    return Outcome.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_outcome())

    def test_persisted_outcome_is_readable_by_id(self, repository):
        outcome = _new_outcome()
        repository.add(outcome)
        assert repository.get(outcome.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(OutcomeId()) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_outcome(self, repository):
        first = _new_outcome()
        second = _new_outcome()
        repository.add(first)
        repository.add(second)
        ids = {o.id for o in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_by_decision_id_filters_correctly(self, repository):
        other_decision_id = DecisionId()
        matching = _new_outcome(decision_id=_DECISION_ID)
        other = _new_outcome(decision_id=other_decision_id)
        repository.add(matching)
        repository.add(other)

        result = repository.list_by_decision_id(_DECISION_ID)

        assert [o.id for o in result] == [matching.id]

    def test_list_all_is_chronological_by_occurred_at_ascending(self, repository):
        occurred_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for occurred_at in occurred_ats:
            repository.add(_new_outcome(occurred_at=occurred_at))

        result = [o.occurred_at for o in repository.list_all()]
        assert result == sorted(occurred_ats)


class TestEqualsOriginal:
    def test_round_tripped_outcome_equals_the_original_in_every_field(self, repository):
        original = _new_outcome()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.case_id == original.case_id
        assert reloaded.decision_id == original.decision_id
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.occurred_at == original.occurred_at
        assert reloaded.recorded_at == original.recorded_at

    def test_occurred_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_outcome()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.occurred_at.utcoffset() == timedelta(hours=2)
        assert reloaded.occurred_at.isoformat() == "2026-10-01T12:00:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_outcome_table_has_no_sql_foreign_key(self, repository):
        column_names = set(outcomes_table.columns.keys())
        assert column_names == {
            "outcome_id",
            "case_id",
            "decision_id",
            "statement",
            "note",
            "occurred_at",
            "recorded_at",
        }
        assert outcomes_table.foreign_keys == set()


class TestCaseOwnership:
    def test_case_id_round_trips(self, repository):
        case_id = CaseId()
        original = _new_outcome(case_id=case_id)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.case_id == case_id

    def test_case_id_not_null_is_enforced(self, repository):
        with pytest.raises(IntegrityError):
            with repository._engine.begin() as connection:
                connection.execute(
                    insert(outcomes_table).values(
                        outcome_id=str(OutcomeId()),
                        decision_id=str(_DECISION_ID),
                        statement="Revenue growth accelerated as expected.",
                        note=None,
                        occurred_at=_OCCURRED_AT.isoformat(),
                        recorded_at=_OCCURRED_AT.isoformat(),
                    )
                )
