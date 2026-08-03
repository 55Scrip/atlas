"""Aggregate persistence tests for Hypothesis: create, persist, read, equals original."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.hypothesis.value_objects import HypothesisId, Statement
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table

_FORMULATED_AT = datetime(2026, 7, 13, 18, 30, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_hypothesis_table(engine)
    return SqlAlchemyHypothesisRepository(engine)


def _new_hypothesis(**overrides) -> Hypothesis:
    defaults = dict(
        statement=Statement(
            "Demand for AI infrastructure may be accelerating faster than the market expects."
        ),
        formulated_at=_FORMULATED_AT,
        note="Revisit after the next reporting cycle.",
    )
    defaults.update(overrides)
    return Hypothesis.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_hypothesis())

    def test_persisted_hypothesis_is_readable_by_id(self, repository):
        hypothesis = _new_hypothesis()
        repository.add(hypothesis)
        assert repository.get(hypothesis.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        unknown = HypothesisId()
        assert repository.get(unknown) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_hypothesis(self, repository):
        first = _new_hypothesis()
        second = _new_hypothesis()
        repository.add(first)
        repository.add(second)
        ids = {h.id for h in repository.list_all()}
        assert ids == {first.id, second.id}

    def test_list_all_is_chronological_by_formulated_at_ascending(self, repository):
        formulated_ats = [
            datetime(2026, 1, 3, tzinfo=timezone.utc),
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
        ]
        for formulated_at in formulated_ats:
            # insert out of chronological order to prove ordering is by
            # formulated_at, not insertion order
            repository.add(_new_hypothesis(formulated_at=formulated_at))

        result = [h.formulated_at for h in repository.list_all()]
        assert result == sorted(formulated_ats)

    def test_chronological_order_compares_true_instant_across_mixed_offsets(self, repository):
        # Two formulated_at values with different UTC offsets that
        # represent nearly the same instant. A naive text/ISO-8601 sort on
        # the stored column would order these incorrectly; a correct
        # implementation compares them as tz-aware datetimes.
        later_but_higher_offset = datetime(2026, 3, 1, 10, 0, tzinfo=timezone(timedelta(hours=5)))
        earlier_but_lower_offset = datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc)
        assert later_but_higher_offset < earlier_but_lower_offset  # sanity check on the fixture

        repository.add(_new_hypothesis(formulated_at=later_but_higher_offset))
        repository.add(_new_hypothesis(formulated_at=earlier_but_lower_offset))

        result = [h.formulated_at for h in repository.list_all()]
        assert result == [later_but_higher_offset, earlier_but_lower_offset]

    def test_tie_breaks_by_recorded_at_then_hypothesis_id(self, repository):
        same_formulated_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
        same_recorded_at = datetime(2026, 2, 2, tzinfo=timezone.utc)
        first = _new_hypothesis(formulated_at=same_formulated_at, clock=lambda: same_recorded_at)
        second = _new_hypothesis(formulated_at=same_formulated_at, clock=lambda: same_recorded_at)
        repository.add(second)
        repository.add(first)

        ordered_ids = [h.id.value for h in repository.list_all()]
        assert ordered_ids == sorted([first.id.value, second.id.value])


class TestEqualsOriginal:
    def test_round_tripped_hypothesis_equals_the_original_in_every_field(self, repository):
        original = _new_hypothesis()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.statement == original.statement
        assert reloaded.note == original.note
        assert reloaded.formulated_at == original.formulated_at
        assert reloaded.recorded_at == original.recorded_at

    def test_optional_note_round_trips_as_none(self, repository):
        original = _new_hypothesis(note=None)
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.note is None

    def test_formulated_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_hypothesis()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded.formulated_at.utcoffset() == timedelta(hours=2)
        assert reloaded.formulated_at.isoformat() == "2026-07-13T18:30:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnly:
    def test_repository_exposes_no_update_or_delete_method(self, repository):
        assert not hasattr(repository, "update")
        assert not hasattr(repository, "delete")


class TestNoForeignKeysOrCoupling:
    def test_hypothesis_table_has_no_columns_referencing_another_aggregate(self, repository):
        from atlas.core.infrastructure.persistence.hypothesis.table import hypotheses_table

        column_names = set(hypotheses_table.columns.keys())
        assert column_names == {
            "hypothesis_id",
            "statement",
            "note",
            "formulated_at",
            "recorded_at",
        }
        assert hypotheses_table.foreign_keys == set()

    def test_existing_core_tables_are_unchanged_by_this_increment(self):
        from atlas.core.infrastructure.persistence.decision.table import decisions_table
        from atlas.core.infrastructure.persistence.decision_context.table import (
            decision_contexts_table,
        )
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
            "observation_id",
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
