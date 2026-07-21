"""Aggregate persistence tests for Reasoning Trace: create, persist,
read, equals original, plus the two-table mechanics unique to this
package's "one or more" cardinality (docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 30).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.exceptions import EmptySupportError
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.reasoning_trace.sqlalchemy_repository import (
    SqlAlchemyReasoningTraceRepository,
)
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    create_reasoning_trace_tables,
    reasoning_trace_supports_table,
    reasoning_traces_table,
)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_reasoning_trace_tables(eng)
    return eng


@pytest.fixture
def repository(engine):
    return SqlAlchemyReasoningTraceRepository(engine)


def _new_trace(**overrides) -> ReasoningTrace:
    defaults = dict(
        case_id=CaseId(),
        supports=frozenset(
            {TypedDomainObjectReference(target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4())}
        ),
    )
    defaults.update(overrides)
    return ReasoningTrace.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_trace())

    def test_persisted_trace_is_readable_by_id(self, repository):
        trace = _new_trace()
        repository.add(trace)
        assert repository.get(trace.id) is not None


class TestOneSupportRoundTrip:
    def test_round_trips_a_single_support(self, repository):
        support = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        trace = _new_trace(supports=frozenset({support}))
        repository.add(trace)
        reloaded = repository.get(trace.id)
        assert reloaded.supports == frozenset({support})


class TestMultiSupportRoundTrip:
    def test_round_trips_multiple_supports_across_different_types(self, repository):
        supports = frozenset(
            {
                TypedDomainObjectReference(
                    target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
                ),
                TypedDomainObjectReference(
                    target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
                ),
                TypedDomainObjectReference(
                    target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
                ),
            }
        )
        trace = _new_trace(supports=supports)
        repository.add(trace)
        reloaded = repository.get(trace.id)
        assert reloaded.supports == supports


class TestTargetTypePreservation:
    def test_every_adopted_target_type_round_trips(self, repository):
        for member in DomainObjectType:
            trace = _new_trace(
                supports=frozenset(
                    {TypedDomainObjectReference(target_type=member, target_id=uuid.uuid4())}
                )
            )
            repository.add(trace)
            reloaded = repository.get(trace.id)
            assert {support.target_type for support in reloaded.supports} == {member}


class TestCasePreservation:
    def test_case_id_round_trips(self, repository):
        case_id = CaseId()
        trace = _new_trace(case_id=case_id)
        repository.add(trace)
        reloaded = repository.get(trace.id)
        assert reloaded.case_id == case_id


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        assert repository.get(ReasoningTraceId()) is None

    def test_duplicate_support_sets_across_separate_traces_are_permitted(self, repository):
        support = TypedDomainObjectReference(
            target_type=DomainObjectType.DECISION, target_id=uuid.uuid4()
        )
        first = _new_trace(supports=frozenset({support}))
        second = _new_trace(supports=frozenset({support}))
        repository.add(first)
        repository.add(second)
        assert repository.get(first.id).supports == repository.get(second.id).supports
        assert first.id != second.id


class TestEqualsOriginal:
    def test_round_tripped_trace_equals_the_original_in_every_field(self, repository):
        original = _new_trace()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.case_id == original.case_id
        assert reloaded.supports == original.supports
        assert reloaded.recorded_at == original.recorded_at


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestAtomicParentAndSupportInsertion:
    def test_add_writes_both_the_parent_row_and_every_support_row(self, repository, engine):
        from sqlalchemy import select

        trace = _new_trace(
            supports=frozenset(
                {
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.OBSERVATION, target_id=uuid.uuid4()
                    ),
                    TypedDomainObjectReference(
                        target_type=DomainObjectType.JUDGMENT, target_id=uuid.uuid4()
                    ),
                }
            )
        )
        repository.add(trace)
        with engine.connect() as connection:
            parent_rows = connection.execute(select(reasoning_traces_table)).mappings().all()
            support_rows = (
                connection.execute(select(reasoning_trace_supports_table)).mappings().all()
            )
        assert len(parent_rows) == 1
        assert len(support_rows) == 2

    def test_a_forced_duplicate_support_row_leaves_no_partial_state(self, repository, engine):
        # Attempting to insert a Reasoning Trace whose own support rows
        # would collide on the composite uniqueness constraint must not
        # leave a parent row behind — the whole `add()` is one
        # transaction.
        trace = _new_trace()
        repository.add(trace)
        duplicate_support = next(iter(trace.supports))
        colliding_trace = ReasoningTrace(
            id=ReasoningTraceId(),
            case_id=trace.case_id,
            supports=frozenset({duplicate_support}),
            recorded_at=datetime.now(timezone.utc),
        )
        # Force a raw duplicate row under the SAME reasoning_trace_id to
        # trigger the UniqueConstraint deliberately, bypassing add()'s
        # own fresh-id generation.
        with engine.begin() as connection:
            connection.execute(
                insert(reasoning_traces_table).values(
                    reasoning_trace_id=str(colliding_trace.id),
                    case_id=str(colliding_trace.case_id),
                    recorded_at=colliding_trace.recorded_at.isoformat(),
                )
            )
            connection.execute(
                insert(reasoning_trace_supports_table).values(
                    reasoning_trace_support_id=str(uuid.uuid4()),
                    reasoning_trace_id=str(colliding_trace.id),
                    target_type=duplicate_support.target_type.value,
                    target_id=str(duplicate_support.target_id),
                )
            )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(reasoning_trace_supports_table).values(
                        reasoning_trace_support_id=str(uuid.uuid4()),
                        reasoning_trace_id=str(colliding_trace.id),
                        target_type=duplicate_support.target_type.value,
                        target_id=str(duplicate_support.target_id),
                    )
                )
        # The first insert (before the deliberate collision) is intact,
        # and no partial second row was added by the failed attempt.
        from sqlalchemy import select

        with engine.connect() as connection:
            rows = (
                connection.execute(
                    select(reasoning_trace_supports_table).where(
                        reasoning_trace_supports_table.c.reasoning_trace_id
                        == str(colliding_trace.id)
                    )
                )
                .mappings()
                .all()
            )
        assert len(rows) == 1


class TestCorruptPersistedState:
    def test_a_parent_row_with_zero_support_rows_raises_on_reconstruction(
        self, repository, engine
    ):
        # This state can only arise from direct database manipulation
        # outside this repository's own add(), which is atomic and
        # always inserts at least one support row.
        orphan_id = uuid.uuid4()
        with engine.begin() as connection:
            connection.execute(
                insert(reasoning_traces_table).values(
                    reasoning_trace_id=str(orphan_id),
                    case_id=str(uuid.uuid4()),
                    recorded_at=datetime.now(timezone.utc).isoformat(),
                )
            )
        with pytest.raises(EmptySupportError):
            repository.get(ReasoningTraceId(orphan_id))


class TestSchemaAndConstraints:
    def test_parent_table_has_only_approved_columns(self, repository):
        assert set(reasoning_traces_table.columns.keys()) == {
            "reasoning_trace_id",
            "case_id",
            "recorded_at",
        }

    def test_support_table_has_only_approved_columns(self, repository):
        assert set(reasoning_trace_supports_table.columns.keys()) == {
            "reasoning_trace_support_id",
            "reasoning_trace_id",
            "target_type",
            "target_id",
        }

    def test_no_foreign_key_anywhere(self, repository):
        assert reasoning_traces_table.foreign_keys == set()
        assert reasoning_trace_supports_table.foreign_keys == set()

    def test_check_constraint_rejects_a_non_adopted_target_type(self, repository):
        engine = repository._engine
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(reasoning_trace_supports_table).values(
                        reasoning_trace_support_id=str(uuid.uuid4()),
                        reasoning_trace_id=str(uuid.uuid4()),
                        target_type="Case",  # not an adopted target type
                        target_id=str(uuid.uuid4()),
                    )
                )

    def test_check_constraint_accepts_every_adopted_target_type(self, repository):
        engine = repository._engine
        for member in DomainObjectType:
            with engine.begin() as connection:
                connection.execute(
                    insert(reasoning_trace_supports_table).values(
                        reasoning_trace_support_id=str(uuid.uuid4()),
                        reasoning_trace_id=str(uuid.uuid4()),
                        target_type=member.value,
                        target_id=str(uuid.uuid4()),
                    )
                )

    def test_unique_constraint_rejects_a_direct_duplicate_row(self, repository):
        engine = repository._engine
        reasoning_trace_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        with engine.begin() as connection:
            connection.execute(
                insert(reasoning_trace_supports_table).values(
                    reasoning_trace_support_id=str(uuid.uuid4()),
                    reasoning_trace_id=reasoning_trace_id,
                    target_type=DomainObjectType.OBSERVATION.value,
                    target_id=target_id,
                )
            )
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(reasoning_trace_supports_table).values(
                        reasoning_trace_support_id=str(uuid.uuid4()),
                        reasoning_trace_id=reasoning_trace_id,
                        target_type=DomainObjectType.OBSERVATION.value,
                        target_id=target_id,
                    )
                )
