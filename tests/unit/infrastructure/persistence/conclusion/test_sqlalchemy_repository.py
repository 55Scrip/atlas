"""Aggregate persistence tests for Conclusion: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.conclusion.entity import Conclusion
from atlas.core.domain.conclusion.value_objects import ConclusionId, Statement
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.infrastructure.persistence.conclusion.sqlalchemy_repository import (
    SqlAlchemyConclusionRepository,
)
from atlas.core.infrastructure.persistence.conclusion.table import create_conclusion_table

_EVIDENCE_ID = EvidenceId()
_CONCLUDED_AT = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_conclusion_table(engine)
    return SqlAlchemyConclusionRepository(engine)


def _new_conclusion(**overrides) -> Conclusion:
    defaults = dict(
        evidence_id=_EVIDENCE_ID,
        statement=Statement("The weight of evidence supports accelerating demand."),
        concluded_at=_CONCLUDED_AT,
        note="Revisit if margins compress next quarter.",
    )
    defaults.update(overrides)
    return Conclusion.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_conclusion())

    def test_persisted_conclusion_is_readable_by_id(self, repository):
        conclusion = _new_conclusion()
        repository.add(conclusion)
        assert repository.get(conclusion.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(ConclusionId()) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_conclusion(self, repository):
        first = _new_conclusion()
        second = _new_conclusion()
        repository.add(first)
        repository.add(second)
        ids = {c.id for c in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_by_evidence_id_filters_correctly(self, repository):
        other_evidence_id = EvidenceId()
        matching = _new_conclusion(evidence_id=_EVIDENCE_ID)
        other = _new_conclusion(evidence_id=other_evidence_id)
        repository.add(matching)
        repository.add(other)

        result = repository.list_by_evidence_id(_EVIDENCE_ID)

        assert [c.id for c in result] == [matching.id]

    def test_list_all_is_chronological_by_concluded_at_ascending(self, repository):
        concluded_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for concluded_at in concluded_ats:
            repository.add(_new_conclusion(concluded_at=concluded_at))

        result = [c.concluded_at for c in repository.list_all()]
        assert result == sorted(concluded_ats)


class TestEqualsOriginal:
    def test_round_tripped_conclusion_equals_the_original_in_every_field(self, repository):
        original = _new_conclusion()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.evidence_id == original.evidence_id
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.concluded_at == original.concluded_at
        assert reloaded.recorded_at == original.recorded_at

    def test_concluded_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_conclusion()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.concluded_at.utcoffset() == timedelta(hours=2)
        assert reloaded.concluded_at.isoformat() == "2026-07-13T12:00:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_conclusion_table_has_no_sql_foreign_key(self, repository):
        from atlas.core.infrastructure.persistence.conclusion.table import conclusions_table

        column_names = set(conclusions_table.columns.keys())
        assert column_names == {
            "conclusion_id",
            "evidence_id",
            "statement",
            "note",
            "concluded_at",
            "recorded_at",
        }
        assert conclusions_table.foreign_keys == set()
