"""Aggregate persistence tests for Case: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.entity import Case
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_case_table(engine)
    return SqlAlchemyCaseRepository(engine)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(Case.create())

    def test_persisted_case_is_readable_by_id(self, repository):
        case = Case.create()
        repository.add(case)
        assert repository.get(case.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(CaseId()) is None

    def test_multiple_cases_remain_distinct(self, repository):
        first = Case.create()
        second = Case.create()
        repository.add(first)
        repository.add(second)
        assert repository.get(first.id).id == first.id
        assert repository.get(second.id).id == second.id
        assert first.id != second.id


class TestEqualsOriginal:
    def test_round_tripped_case_equals_the_original_in_every_field(self, repository):
        original = Case.create()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.id == original.id
        assert reloaded.recorded_at == original.recorded_at

    def test_persisted_identity_is_unchanged(self, repository):
        original = Case.create()
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.id.value == original.id.value

    def test_persisted_recorded_at_is_unchanged(self, repository):
        fixed = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
        original = Case.create(clock=lambda: fixed)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.recorded_at == fixed


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_case_table_has_only_approved_columns(self, repository):
        from atlas.core.infrastructure.persistence.case.table import cases_table

        assert set(cases_table.columns.keys()) == {"case_id", "recorded_at"}
        assert cases_table.foreign_keys == set()

    def test_existing_core_tables_are_unchanged_by_this_package(self):
        from atlas.core.infrastructure.persistence.decision.table import decisions_table
        from atlas.core.infrastructure.persistence.outcome.table import outcomes_table

        # No case_id column was added to any existing aggregate table —
        # DO-IMP-001's own scope forbids that (reserved for a later,
        # separately-reviewed package).
        assert set(decisions_table.columns.keys()) == {
            "id",
            "user_id",
            "decision_type",
            "subject",
            "reason",
            "confidence",
            "decided_at",
            "recorded_at",
            "source",
        }
        assert set(outcomes_table.columns.keys()) == {
            "outcome_id",
            "decision_id",
            "statement",
            "note",
            "occurred_at",
            "recorded_at",
        }
