"""Aggregate persistence tests: create, persist, read, equals original."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.core.domain.case.value_objects import CaseId
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
        case_id=CaseId(),
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
        assert reloaded.case_id == original.case_id
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


class TestCaseOwnership:
    def test_same_reason_in_different_cases_is_permitted(self, repository):
        first = _new_decision()
        second = _new_decision()
        repository.add(first)
        repository.add(second)
        assert first.case_id != second.case_id
        assert repository.get(first.id).investment_case == repository.get(
            second.id
        ).investment_case

    def test_duplicate_reason_in_one_case_is_permitted(self, repository):
        case_id = CaseId()
        first = _new_decision(case_id=case_id)
        second = _new_decision(case_id=case_id)
        repository.add(first)
        repository.add(second)
        assert repository.get(first.id).case_id == repository.get(second.id).case_id
        assert first.id != second.id

    def test_case_id_not_null_is_enforced(self, repository):
        from sqlalchemy import insert
        from sqlalchemy.exc import IntegrityError

        from atlas.core.domain.decision.value_objects import DecisionId
        from atlas.core.infrastructure.persistence.decision.table import decisions_table

        engine = repository._engine
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(
                    insert(decisions_table).values(
                        id=str(DecisionId()),
                        case_id=None,
                        user_id=str(uuid.uuid4()),
                        decision_type="BUY",
                        subject="ASML",
                        reason="Durable moat, undervalued relative to peers",
                        confidence=75,
                        decided_at=datetime(2026, 7, 1, tzinfo=timezone.utc).isoformat(),
                        recorded_at=datetime(2026, 7, 1, tzinfo=timezone.utc).isoformat(),
                        source="Manual",
                    )
                )
