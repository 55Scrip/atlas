"""Aggregate persistence tests for Judgment: create, persist, read,
equals original.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.judgment.sqlalchemy_repository import (
    SqlAlchemyJudgmentRepository,
)
from atlas.core.infrastructure.persistence.judgment.table import (
    create_judgment_table,
    judgments_table,
)


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_judgment_table(engine)
    return SqlAlchemyJudgmentRepository(engine)


def _new_judgment(**overrides) -> Judgment:
    defaults = dict(
        case_id=CaseId(),
        characterization=Characterization("settled characterization"),
    )
    defaults.update(overrides)
    return Judgment.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_judgment())

    def test_persisted_judgment_is_readable_by_id(self, repository):
        judgment = _new_judgment()
        repository.add(judgment)
        assert repository.get(judgment.id) is not None

    def test_persists_the_internal_content_form_with_no_subject(self, repository):
        judgment = _new_judgment()
        repository.add(judgment)
        reloaded = repository.get(judgment.id)
        assert reloaded.subject is None

    def test_persists_the_referential_form_with_a_subject(self, repository):
        subject = TypedDomainObjectReference(
            target_type=DomainObjectType.KNOWLEDGE_REFERENCE, target_id=uuid.uuid4()
        )
        judgment = _new_judgment(subject=subject)
        repository.add(judgment)
        reloaded = repository.get(judgment.id)
        assert reloaded.subject == subject


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(JudgmentId()) is None

    def test_duplicate_subject_references_across_separate_records_are_permitted(self, repository):
        subject = TypedDomainObjectReference(
            target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
        )
        first = _new_judgment(subject=subject)
        second = _new_judgment(subject=subject)
        repository.add(first)
        repository.add(second)
        assert repository.get(first.id).subject == repository.get(second.id).subject
        assert first.id != second.id


class TestEqualsOriginal:
    def test_round_tripped_judgment_equals_the_original_in_every_field(self, repository):
        original = _new_judgment()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.case_id == original.case_id
        assert reloaded.characterization == original.characterization
        assert reloaded.subject == original.subject
        assert reloaded.recorded_at == original.recorded_at

    def test_every_adopted_subject_target_type_round_trips(self, repository):
        for member in DomainObjectType:
            judgment = _new_judgment(
                subject=TypedDomainObjectReference(target_type=member, target_id=uuid.uuid4())
            )
            repository.add(judgment)
            reloaded = repository.get(judgment.id)
            assert reloaded.subject.target_type is member


class TestReadAll:
    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_judgment(self, repository):
        first = _new_judgment()
        second = _new_judgment()
        repository.add(first)
        repository.add(second)
        assert {judgment.id for judgment in repository.list_all()} == {first.id, second.id}


class TestDelete:
    def test_delete_removes_the_record(self, repository):
        judgment = _new_judgment()
        repository.add(judgment)
        repository.delete(judgment.id)
        assert repository.get(judgment.id) is None

    def test_delete_removes_only_the_targeted_record(self, repository):
        first = _new_judgment()
        second = _new_judgment()
        repository.add(first)
        repository.add(second)
        repository.delete(first.id)
        assert repository.get(first.id) is None
        assert repository.get(second.id) is not None

    def test_delete_is_idempotent_for_an_unknown_id(self, repository):
        repository.delete(JudgmentId())

    def test_delete_then_reload_reflects_the_deletion_in_list_all(self, repository):
        judgment = _new_judgment()
        repository.add(judgment)
        repository.delete(judgment.id)
        assert judgment.id not in {j.id for j in repository.list_all()}


class TestInsertAndDeleteOnly:
    def test_repository_exposes_no_update_method(self, repository):
        assert not hasattr(repository, "update")

    def test_repository_exposes_a_delete_method(self, repository):
        assert hasattr(repository, "delete")


class TestSchemaAndConstraints:
    def test_table_has_only_approved_columns(self, repository):
        assert set(judgments_table.columns.keys()) == {
            "judgment_id",
            "case_id",
            "characterization",
            "subject_target_type",
            "subject_target_id",
            "recorded_at",
        }

    def test_no_foreign_key_across_the_polymorphic_reference(self, repository):
        assert judgments_table.foreign_keys == set()

    def test_check_constraint_rejects_a_non_adopted_subject_target_type(self, repository):
        engine = repository._engine
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(judgments_table).values(
                        judgment_id=str(uuid.uuid4()),
                        case_id=str(uuid.uuid4()),
                        characterization="settled",
                        subject_target_type="Case",  # not an adopted target type
                        subject_target_id=str(uuid.uuid4()),
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                    )
                )

    def test_check_constraint_accepts_every_adopted_subject_target_type(self, repository):
        engine = repository._engine
        for member in DomainObjectType:
            with engine.begin() as connection:
                connection.execute(
                    insert(judgments_table).values(
                        judgment_id=str(uuid.uuid4()),
                        case_id=str(uuid.uuid4()),
                        characterization="settled",
                        subject_target_type=member.value,
                        subject_target_id=str(uuid.uuid4()),
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                    )
                )

    def test_check_constraint_accepts_a_wholly_null_subject_reference(self, repository):
        engine = repository._engine
        with engine.begin() as connection:
            connection.execute(
                insert(judgments_table).values(
                    judgment_id=str(uuid.uuid4()),
                    case_id=str(uuid.uuid4()),
                    characterization="settled",
                    subject_target_type=None,
                    subject_target_id=None,
                    recorded_at=datetime.now(timezone.utc).isoformat(),
                )
            )

    def test_check_constraint_rejects_a_partially_null_subject_reference(self, repository):
        engine = repository._engine
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(judgments_table).values(
                        judgment_id=str(uuid.uuid4()),
                        case_id=str(uuid.uuid4()),
                        characterization="settled",
                        subject_target_type=DomainObjectType.JUDGMENT.value,
                        subject_target_id=None,
                        recorded_at=datetime.now(timezone.utc).isoformat(),
                    )
                )


class TestPreviouslyImplementedInfrastructureUnchanged:
    """Regression: DO-IMP-001 (Case), DO-IMP-002 (shared typed-reference
    infrastructure), and DO-IMP-003 (Knowledge Reference) remain
    unaffected by this package.
    """

    def test_case_table_unchanged(self):
        from atlas.core.infrastructure.persistence.case.table import cases_table

        assert set(cases_table.columns.keys()) == {"case_id", "recorded_at"}

    def test_knowledge_reference_table_unchanged(self):
        from atlas.core.infrastructure.persistence.knowledge_reference.table import (
            knowledge_references_table,
        )

        assert set(knowledge_references_table.columns.keys()) == {
            "knowledge_reference_id",
            "case_id",
            "target_type",
            "target_id",
            "recorded_at",
        }

    def test_domain_object_type_still_has_exactly_six_members(self):
        assert {member.value for member in DomainObjectType} == {
            "Observation",
            "KnowledgeReference",
            "ReasoningTrace",
            "Judgment",
            "Decision",
            "Outcome",
        }

    def test_typed_domain_object_reference_unchanged(self):
        reference = TypedDomainObjectReference(
            target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
        )
        assert reference.target_type is DomainObjectType.OBSERVATION
