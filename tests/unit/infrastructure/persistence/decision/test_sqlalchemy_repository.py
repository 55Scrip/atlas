"""Aggregate persistence tests: create, persist, read, equals original."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@pytest.fixture
def repository():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_decision_table(engine)
    return SqlAlchemyDecisionRepository(engine)


def _new_decision(**overrides) -> Decision:
    defaults = dict(
        user_id=UserId(uuid.uuid4()),
        decision_type=DecisionType.BUY,
        subject=Subject("ASML"),
        investment_case=InvestmentCase("Durable moat, undervalued relative to peers"),
        confidence=Confidence(75),
        decided_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        source=DecisionSource.MANUAL,
    )
    defaults.update(overrides)
    return Decision.register(**defaults)


class TestCreateAndPersist:
    def test_add_does_not_raise(self, repository):
        repository.add(_new_decision())

    def test_persisted_decision_is_readable_by_id(self, repository):
        decision = _new_decision()
        repository.add(decision)
        assert repository.get(decision.id) is not None


class TestRead:
    def test_get_returns_none_for_unknown_id(self, repository):
        unknown = _new_decision().id
        assert repository.get(unknown) is None

    def test_list_all_is_empty_initially(self, repository):
        assert repository.list_all() == []

    def test_list_all_returns_every_recorded_decision(self, repository):
        first = _new_decision()
        second = _new_decision()
        repository.add(first)
        repository.add(second)
        ids = {decision.id for decision in repository.list_all()}
        assert ids == {first.id, second.id}


class TestEqualsOriginal:
    def test_round_tripped_decision_equals_the_original_in_every_field(self, repository):
        original = _new_decision()
        repository.add(original)
        reloaded = repository.get(original.id)

        assert reloaded == original
        assert reloaded.user_id == original.user_id
        assert reloaded.decision_type == original.decision_type
        assert reloaded.investment_case == original.investment_case
        assert reloaded.confidence == original.confidence
        assert reloaded.decided_at == original.decided_at
        assert reloaded.recorded_at == original.recorded_at
        assert reloaded.subject == original.subject
        assert reloaded.source == original.source

    def test_subject_round_trips_with_a_different_value(self, repository):
        original = _new_decision(subject=Subject("MSFT"))
        repository.add(original)
        reloaded = repository.get(original.id)
        assert reloaded.subject == Subject("MSFT")
