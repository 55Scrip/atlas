"""Tests for `atlas.alpha.investment_case_lifecycle.repository
.SqlAlchemyLifecycleSnapshotRepository` -- round-trip fidelity of the
one persisted concept this package owns, mirroring
`tests/unit/alpha/decision_readiness/test_repository.py`'s own shape
were one to exist (this package's sibling repositories are exercised
indirectly through their own service tests; this one gets a direct
round-trip test since `LifecycleSnapshot` carries a nested
`MandatoryCoreAssessment` structure worth verifying byte-for-byte)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case_lifecycle.models import (
    LifecycleSnapshot,
    LifecycleState,
    MandatoryCoreAssessment,
    MandatoryItemAssessment,
    MandatoryItemId,
    MissingReasonCode,
)
from atlas.alpha.investment_case_lifecycle.repository import SqlAlchemyLifecycleSnapshotRepository
from atlas.alpha.investment_case_lifecycle.table import create_investment_case_lifecycle_history_table

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_investment_case_lifecycle_history_table(engine)
    return engine


def _snapshot(case_id="case-1", *, all_satisfied=True) -> LifecycleSnapshot:
    items = tuple(
        MandatoryItemAssessment(
            item=item_id,
            satisfied=all_satisfied,
            satisfied_via="growth" if all_satisfied else None,
            reason=None if all_satisfied else MissingReasonCode.WAITING_FOR_CURRENT_ECONOMICS,
        )
        for item_id in MandatoryItemId
    )
    return LifecycleSnapshot(
        case_id=case_id,
        lifecycle_state=LifecycleState.PUBLISHED if all_satisfied else LifecycleState.ANALYSIS_RUNNING,
        mandatory_core=MandatoryCoreAssessment(items=items, all_satisfied=all_satisfied),
        published_since=NOW if all_satisfied else None,
        generated_at=NOW,
    )


class TestRoundTrip:
    def test_get_returns_none_for_unknown_case(self):
        repository = SqlAlchemyLifecycleSnapshotRepository(_engine())
        assert repository.get("does-not-exist") is None

    def test_upsert_then_get_round_trips_exactly(self):
        repository = SqlAlchemyLifecycleSnapshotRepository(_engine())
        snapshot = _snapshot()
        repository.upsert(snapshot, ticker="ASML")
        fetched = repository.get("case-1")
        assert fetched == snapshot

    def test_upsert_replaces_previous_row_for_same_case(self):
        repository = SqlAlchemyLifecycleSnapshotRepository(_engine())
        repository.upsert(_snapshot(all_satisfied=True), ticker="ASML")
        repository.upsert(_snapshot(all_satisfied=False), ticker="ASML")
        fetched = repository.get("case-1")
        assert fetched.lifecycle_state is LifecycleState.ANALYSIS_RUNNING
        assert fetched.mandatory_core.all_satisfied is False

    def test_list_all_returns_every_persisted_case(self):
        repository = SqlAlchemyLifecycleSnapshotRepository(_engine())
        repository.upsert(_snapshot(case_id="case-1"), ticker="ASML")
        repository.upsert(_snapshot(case_id="case-2"), ticker="NVDA")
        all_snapshots = repository.list_all()
        assert {s.case_id for s in all_snapshots} == {"case-1", "case-2"}
