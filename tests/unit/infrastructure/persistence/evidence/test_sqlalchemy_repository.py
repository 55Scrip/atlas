"""Aggregate persistence tests for Evidence: create, persist, read, equals original."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table

_OBSERVED_AT = datetime(2026, 7, 13, 9, 15, 0, tzinfo=timezone(timedelta(hours=2)))
_OBSERVATION_ID = ObservationId()


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_evidence_table(engine)
    return SqlAlchemyEvidenceRepository(engine)


def _new_evidence(**overrides) -> Evidence:
    defaults = dict(
        observation_id=_OBSERVATION_ID,
        statement=Statement(
            "Order intake increased by 24 percent and management raised "
            "full-year guidance for the second consecutive quarter."
        ),
        direction=Direction.SUPPORTS,
        observed_at=_OBSERVED_AT,
        source="Quarterly earnings report",
        note="The comparison benefits from a weak prior-year period.",
    )
    defaults.update(overrides)
    return Evidence.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_evidence())

    def test_persisted_evidence_is_readable_by_id(self, repository):
        evidence = _new_evidence()
        repository.add(evidence)
        assert repository.get(evidence.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        unknown = EvidenceId()
        assert repository.get(unknown) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_evidence(self, repository):
        first = _new_evidence()
        second = _new_evidence(direction=Direction.CHALLENGES)
        repository.add(first)
        repository.add(second)
        ids = {e.id for e in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_all_is_chronological_by_observed_at_ascending(self, repository):
        observed_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for observed_at in observed_ats:
            # insert out of chronological order to prove ordering is by
            # observed_at, not insertion order
            repository.add(_new_evidence(observed_at=observed_at))

        result = [e.observed_at for e in repository.list_all()]
        assert result == sorted(observed_ats)

    def test_chronological_order_compares_true_instant_across_mixed_offsets(self, repository):
        # Two observed_at values with different UTC offsets. A naive
        # text/ISO-8601 sort on the stored column would order these
        # incorrectly; a correct implementation compares them as
        # tz-aware datetimes.
        later_but_higher_offset = datetime(2026, 3, 1, 10, 0, tzinfo=timezone(timedelta(hours=5)))
        earlier_but_lower_offset = datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc)
        assert later_but_higher_offset < earlier_but_lower_offset  # sanity check on the fixture

        repository.add(_new_evidence(observed_at=later_but_higher_offset))
        repository.add(_new_evidence(observed_at=earlier_but_lower_offset))

        result = [e.observed_at for e in repository.list_all()]
        assert result == [later_but_higher_offset, earlier_but_lower_offset]

    def test_tie_breaks_by_recorded_at_then_evidence_id(self, repository):
        same_observed_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
        same_recorded_at = datetime(2026, 2, 2, tzinfo=timezone.utc)
        first = _new_evidence(observed_at=same_observed_at, clock=lambda: same_recorded_at)
        second = _new_evidence(observed_at=same_observed_at, clock=lambda: same_recorded_at)
        repository.add(second)
        repository.add(first)

        ordered_ids = [e.id.value for e in repository.list_all()]
        assert ordered_ids == sorted([first.id.value, second.id.value])


class TestEqualsOriginal:
    def test_round_tripped_evidence_equals_the_original_in_every_field(self, repository):
        original = _new_evidence()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.observation_id == original.observation_id
        assert reloaded.statement == original.statement
        assert reloaded.direction == original.direction
        assert reloaded.source == original.source
        assert reloaded.note == original.note
        assert reloaded.observed_at == original.observed_at
        assert reloaded.recorded_at == original.recorded_at

    def test_challenges_direction_round_trips(self, repository):
        original = _new_evidence(direction=Direction.CHALLENGES)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.direction == Direction.CHALLENGES

    def test_optional_fields_round_trip_as_none(self, repository):
        original = _new_evidence(source=None, note=None)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.source is None
        assert reloaded.note is None

    def test_observed_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_evidence()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.observed_at.utcoffset() == timedelta(hours=2)
        assert reloaded.observed_at.isoformat() == "2026-07-13T09:15:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertAndDeleteOnly:
    """Atlas Alpha, Evidence Sprint 1: `delete` is now supported (the first
    delete capability in this codebase's persistence layer); `update`
    remains unsupported, matching every other aggregate."""

    def test_repository_exposes_no_update_method(self, repository):
        assert not hasattr(repository, "update")

    def test_repository_exposes_a_delete_method(self, repository):
        assert hasattr(repository, "delete")


class TestDelete:
    def test_delete_removes_the_record(self, repository):
        evidence = _new_evidence()
        repository.add(evidence)
        repository.delete(evidence.id)
        assert repository.get(evidence.id) is None

    def test_delete_removes_only_the_targeted_record(self, repository):
        keep = _new_evidence()
        remove = _new_evidence()
        repository.add(keep)
        repository.add(remove)
        repository.delete(remove.id)
        assert repository.get(keep.id) == keep
        assert [e.id for e in repository.list_all()] == [keep.id]

    def test_delete_is_idempotent_for_an_unknown_id(self, repository):
        repository.delete(EvidenceId())  # must not raise

    def test_delete_then_reload_reflects_the_deletion_in_list_all(self, repository):
        evidence = _new_evidence()
        repository.add(evidence)
        repository.delete(evidence.id)
        assert repository.list_all() == []


class TestObservationAnchorAndNoOtherCoupling:
    def test_evidence_table_has_exactly_the_expected_columns(self, repository):
        from atlas.core.infrastructure.persistence.evidence.table import evidence_table

        column_names = set(evidence_table.columns.keys())
        assert column_names == {
            "evidence_id",
            "observation_id",
            "statement",
            "direction",
            "source",
            "note",
            "observed_at",
            "recorded_at",
        }
        # observation_id is a plain indexed column (Interpretation's own
        # established convention), never a SQL ForeignKey.
        assert evidence_table.foreign_keys == set()
        assert evidence_table.name == "evidence"

    def test_existing_core_tables_are_unchanged_by_this_increment(self):
        from atlas.core.infrastructure.persistence.decision.table import decisions_table
        from atlas.core.infrastructure.persistence.decision_context.table import (
            decision_contexts_table,
        )
        from atlas.core.infrastructure.persistence.hypothesis.table import hypotheses_table
        from atlas.core.infrastructure.persistence.observation.table import observations_table

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
        assert set(decision_contexts_table.columns.keys()) == {
            "context_id",
            "decision_id",
            "situation",
            "portfolio_relevance",
            "capital_considerations",
            "alternatives_considered",
            "uncertainties",
            "captured_at",
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
        assert set(hypotheses_table.columns.keys()) == {
            "hypothesis_id",
            "statement",
            "note",
            "formulated_at",
            "recorded_at",
        }
