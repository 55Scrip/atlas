"""Aggregate persistence tests for Knowledge Reference: create, persist,
read, equals original.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.knowledge_reference.sqlalchemy_repository import (
    SqlAlchemyKnowledgeReferenceRepository,
)
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    create_knowledge_reference_table,
    knowledge_references_table,
)


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_knowledge_reference_table(engine)
    return SqlAlchemyKnowledgeReferenceRepository(engine)


def _new_kr(**overrides) -> KnowledgeReference:
    defaults = dict(
        case_id=CaseId(),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
        ),
    )
    defaults.update(overrides)
    return KnowledgeReference.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_kr())

    def test_persisted_knowledge_reference_is_readable_by_id(self, repository):
        kr = _new_kr()
        repository.add(kr)
        assert repository.get(kr.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(KnowledgeReferenceId()) is None

    def test_duplicate_targets_across_separate_records_are_permitted(self, repository):
        target = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        first = _new_kr(target=target)
        second = _new_kr(target=target)
        repository.add(first)
        repository.add(second)
        assert repository.get(first.id).target == repository.get(second.id).target
        assert first.id != second.id


class TestEqualsOriginal:
    def test_round_tripped_reference_equals_the_original_in_every_field(self, repository):
        original = _new_kr()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.case_id == original.case_id
        assert reloaded.target == original.target
        assert reloaded.recorded_at == original.recorded_at

    def test_every_adopted_target_type_round_trips(self, repository):
        for member in DomainObjectType:
            kr = _new_kr(
                target=TypedDomainObjectReference(target_type=member, target_id=uuid.uuid4())
            )
            repository.add(kr)
            reloaded = repository.get(kr.id)
            assert reloaded.target.target_type is member


class TestReadAll:
    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_reference(self, repository):
        first = _new_kr()
        second = _new_kr()
        repository.add(first)
        repository.add(second)
        ids = {k.id for k in repository.list_all()}
        assert ids == {first.id, second.id}


class TestDelete:
    def test_delete_removes_the_record(self, repository):
        kr = _new_kr()
        repository.add(kr)
        repository.delete(kr.id)
        assert repository.get(kr.id) is None

    def test_delete_removes_only_the_targeted_record(self, repository):
        keep = _new_kr()
        remove = _new_kr()
        repository.add(keep)
        repository.add(remove)
        repository.delete(remove.id)
        assert repository.get(keep.id) == keep
        assert [k.id for k in repository.list_all()] == [keep.id]

    def test_delete_is_idempotent_for_an_unknown_id(self, repository):
        repository.delete(KnowledgeReferenceId())  # must not raise

    def test_delete_then_reload_reflects_the_deletion_in_list_all(self, repository):
        kr = _new_kr()
        repository.add(kr)
        repository.delete(kr.id)
        assert repository.list_all() == []


class TestInsertAndDeleteOnly:
    """Atlas Alpha, Knowledge Reference Sprint 1: `delete` is now
    supported (mirroring Evidence's own identical addition in Evidence
    Sprint 1); `update` remains unsupported, matching every other
    aggregate."""

    def test_repository_exposes_no_update_method(self, repository):
        assert not hasattr(repository, "update")

    def test_repository_exposes_a_delete_method(self, repository):
        assert hasattr(repository, "delete")


class TestSchemaAndConstraints:
    def test_table_has_only_approved_columns(self, repository):
        assert set(knowledge_references_table.columns.keys()) == {
            "knowledge_reference_id",
            "case_id",
            "target_type",
            "target_id",
            "recorded_at",
        }

    def test_no_foreign_key_across_the_polymorphic_reference(self, repository):
        assert knowledge_references_table.foreign_keys == set()

    def test_check_constraint_rejects_a_non_adopted_target_type(self, repository):
        engine = repository._engine
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(knowledge_references_table).values(
                        knowledge_reference_id=str(uuid.uuid4()),
                        case_id=str(uuid.uuid4()),
                        target_type="Case",  # not an adopted target type
                        target_id=str(uuid.uuid4()),
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                    )
                )

    def test_check_constraint_accepts_every_adopted_target_type(self, repository):
        engine = repository._engine
        for member in DomainObjectType:
            with engine.begin() as connection:
                connection.execute(
                    insert(knowledge_references_table).values(
                        knowledge_reference_id=str(uuid.uuid4()),
                        case_id=str(uuid.uuid4()),
                        target_type=member.value,
                        target_id=str(uuid.uuid4()),
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                    )
                )


class TestExistingCoreTablesAreUnchanged:
    def test_case_decision_outcome_observation_tables_unaffected(self):
        from atlas.core.infrastructure.persistence.case.table import cases_table
        from atlas.core.infrastructure.persistence.decision.table import decisions_table
        from atlas.core.infrastructure.persistence.observation.table import observations_table
        from atlas.core.infrastructure.persistence.outcome.table import outcomes_table

        assert set(cases_table.columns.keys()) == {"case_id", "recorded_at"}
        assert set(decisions_table.columns.keys()) == {
            "id",
            "case_id",
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
            "case_id",
            "decision_id",
            "statement",
            "note",
            "occurred_at",
            "recorded_at",
        }
        assert set(observations_table.columns.keys()) == {
            "observation_id",
            "case_id",
            "subject",
            "statement",
            "source",
            "note",
            "observed_at",
            "recorded_at",
        }
