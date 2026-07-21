"""Tests for SqlAlchemyInvestorIdentityRepository (ATLAS-009B).

Covers the three behaviors this capability exists for: fresh-store
initialization, atomic reconciliation of legacy session-derived
`Decision.user_id` values, and idempotent fast-path behavior on later
calls (no re-reconciliation).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, insert, select
from sqlalchemy.pool import StaticPool

from atlas.core.domain.decision.value_objects import UserId
from atlas.core.infrastructure.persistence.decision.table import (
    create_decision_table,
    decisions_table,
)
from atlas.core.infrastructure.persistence.investor_identity.sqlalchemy_repository import (
    SqlAlchemyInvestorIdentityRepository,
)
from atlas.core.infrastructure.persistence.investor_identity.table import (
    create_investor_identity_table,
    investor_identity_table,
)

_RECORDED_AT = datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_investor_identity_table(eng)
    create_decision_table(eng)
    return eng


@pytest.fixture
def repository(engine):
    return SqlAlchemyInvestorIdentityRepository(engine)


def _insert_legacy_decision(engine, user_id: uuid.UUID) -> str:
    decision_id = str(uuid.uuid4())
    with engine.begin() as connection:
        connection.execute(
            insert(decisions_table).values(
                id=decision_id,
                case_id=str(uuid.uuid4()),
                user_id=str(user_id),
                decision_type="BUY",
                subject="NVIDIA",
                reason="Demand accelerating.",
                confidence=80,
                decided_at=_RECORDED_AT.isoformat(),
                recorded_at=_RECORDED_AT.isoformat(),
                source="MANUAL",
            )
        )
    return decision_id


def _all_decision_user_ids(engine) -> list[str]:
    with engine.connect() as connection:
        rows = connection.execute(select(decisions_table.c.user_id)).all()
    return [row[0] for row in rows]


class TestFreshStoreInitialization:
    def test_resolve_returns_a_user_id(self, repository):
        user_id = repository.resolve()
        assert isinstance(user_id, UserId)

    def test_resolve_persists_exactly_one_row(self, engine, repository):
        repository.resolve()
        with engine.connect() as connection:
            rows = connection.execute(select(investor_identity_table)).mappings().all()
        assert len(rows) == 1
        assert rows[0]["id"] == "singleton"

    def test_resolve_on_fresh_store_leaves_no_decisions_to_reconcile(self, engine, repository):
        repository.resolve()
        assert _all_decision_user_ids(engine) == []


class TestLegacyReconciliation:
    def test_resolve_reconciles_distinct_legacy_user_ids_to_one_value(self, engine, repository):
        _insert_legacy_decision(engine, uuid.uuid4())
        _insert_legacy_decision(engine, uuid.uuid4())
        _insert_legacy_decision(engine, uuid.uuid4())

        resolved = repository.resolve()

        user_ids = _all_decision_user_ids(engine)
        assert len(user_ids) == 3
        assert set(user_ids) == {str(resolved)}

    def test_resolve_on_a_store_with_no_decisions_yet_is_a_harmless_no_op(
        self, engine, repository
    ):
        resolved = repository.resolve()
        assert _all_decision_user_ids(engine) == []
        assert isinstance(resolved, UserId)


class TestIdempotentFastPath:
    def test_second_resolve_returns_the_same_user_id(self, repository):
        first = repository.resolve()
        second = repository.resolve()
        assert first == second

    def test_second_resolve_does_not_reconcile_decisions_added_after_first_resolve(
        self, engine, repository
    ):
        repository.resolve()

        # A Decision inserted after the store already has an InvestorIdentity —
        # simulating a bug elsewhere, or a row an operator edited by hand.
        # The fast path must be a pure read: it must never touch decisions_table.
        other_user_id = uuid.uuid4()
        decision_id = _insert_legacy_decision(engine, other_user_id)

        repository.resolve()

        with engine.connect() as connection:
            row = (
                connection.execute(
                    select(decisions_table).where(decisions_table.c.id == decision_id)
                )
                .mappings()
                .first()
            )
        assert row["user_id"] == str(other_user_id)
