"""Aggregate persistence tests for DecisionContext: create, persist, read, equals original."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.domain.decision_context.exceptions import DuplicateDecisionContextError
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    Situation,
    Uncertainties,
)
from atlas.core.infrastructure.persistence.decision_context.sqlalchemy_repository import (
    SqlAlchemyDecisionContextRepository,
)
from atlas.core.infrastructure.persistence.decision_context.table import (
    create_decision_context_table,
)

_CAPTURED_AT = datetime(2026, 6, 17, 0, 54, 0, tzinfo=timezone(timedelta(hours=2)))


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_context_table(engine)
    return SqlAlchemyDecisionContextRepository(engine)


def _new_context(**overrides) -> DecisionContext:
    defaults = dict(
        decision_id=DecisionId(uuid.uuid4()),
        situation=Situation("Large semiconductor exposure already; wanted to preserve cash."),
        captured_at=_CAPTURED_AT,
        portfolio_relevance="Would complement existing holdings",
        capital_considerations="Only part of available capital should be deployed",
        alternatives_considered=AlternativesConsidered(("Buy Arm", "Wait until after the Fed")),
        uncertainties=Uncertainties(("Short-term market reaction",)),
    )
    defaults.update(overrides)
    return DecisionContext.capture(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_context())

    def test_persisted_context_is_readable_by_decision_id(self, repository):
        context = _new_context()
        repository.add(context)
        assert repository.get_by_decision_id(context.decision_id) is not None


class TestRead:
    def test_get_returns_none_when_no_context_exists(self, repository):
        unknown_decision_id = DecisionId(uuid.uuid4())
        assert repository.get_by_decision_id(unknown_decision_id) is None


class TestEqualsOriginal:
    def test_round_tripped_context_equals_the_original_in_every_field(self, repository):
        original = _new_context()
        repository.add(original)
        reloaded = repository.get_by_decision_id(original.decision_id)

        assert reloaded == original
        assert reloaded.context_id == original.context_id
        assert reloaded.decision_id == original.decision_id
        assert reloaded.situation == original.situation
        assert reloaded.portfolio_relevance == original.portfolio_relevance
        assert reloaded.capital_considerations == original.capital_considerations
        assert reloaded.alternatives_considered == original.alternatives_considered
        assert reloaded.uncertainties == original.uncertainties
        assert reloaded.captured_at == original.captured_at
        assert reloaded.recorded_at == original.recorded_at

    def test_optional_fields_round_trip_as_none(self, repository):
        original = _new_context(portfolio_relevance=None, capital_considerations=None)
        repository.add(original)
        reloaded = repository.get_by_decision_id(original.decision_id)
        assert reloaded.portfolio_relevance is None
        assert reloaded.capital_considerations is None

    def test_empty_collections_round_trip_as_empty(self, repository):
        original = _new_context(
            alternatives_considered=AlternativesConsidered(), uncertainties=Uncertainties()
        )
        repository.add(original)
        reloaded = repository.get_by_decision_id(original.decision_id)
        assert reloaded.alternatives_considered == AlternativesConsidered()
        assert reloaded.uncertainties == Uncertainties()

    def test_captured_at_offset_round_trips_exactly_unlike_utc_recorded_at(self, repository):
        original = _new_context()
        repository.add(original)
        reloaded = repository.get_by_decision_id(original.decision_id)

        assert reloaded.captured_at.utcoffset() == timedelta(hours=2)
        assert reloaded.captured_at.isoformat() == "2026-06-17T00:54:00+02:00"
        assert reloaded.recorded_at.utcoffset() == timedelta(0)


class TestInsertOnlyBehavior:
    def test_one_context_per_decision_is_enforced_at_the_database_level(self, repository):
        decision_id = DecisionId(uuid.uuid4())
        repository.add(_new_context(decision_id=decision_id))

        with pytest.raises(DuplicateDecisionContextError):
            repository.add(_new_context(decision_id=decision_id))

    def test_different_decisions_may_each_have_their_own_context(self, repository):
        first = _new_context()
        second = _new_context()
        repository.add(first)
        repository.add(second)

        assert repository.get_by_decision_id(first.decision_id) is not None
        assert repository.get_by_decision_id(second.decision_id) is not None
