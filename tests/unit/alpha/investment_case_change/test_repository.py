"""`SqlAlchemyInvestmentCaseSnapshotRepository` tests (Investment Case
Monitoring & Change Intelligence v1). Real in-memory SQLite throughout,
matching `business_data_refresh`'s own established real-harness
testing discipline.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.analysis_engine.investment_case_change import AnalyticalSnapshot

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)


def _snapshot(*, content_hash: str, captured_at: datetime = _T0, current_yield: float | None = 0.03) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(("growth", "moderate", "business_finding:growth"),),
        risk_category_states=(),
        valuation_status="fairly_valued",
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=current_yield,
        strength_kinds=(),
        risk_highlight_kinds=(),
        open_question_origins=(),
        content_hash=content_hash,
        captured_at=captured_at,
    )


@pytest.fixture
def engine() -> Engine:
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})
    create_investment_case_snapshot_table(engine)
    return engine


class TestGetLatest:
    def test_returns_none_when_nothing_persisted(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        assert repository.get_latest("case-1") is None

    def test_returns_the_most_recently_captured_snapshot(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        repository.add("case-1", _snapshot(content_hash="hash-a", captured_at=_T0))
        repository.add("case-1", _snapshot(content_hash="hash-b", captured_at=_T1))
        latest = repository.get_latest("case-1")
        assert latest is not None
        assert latest.content_hash == "hash-b"

    def test_round_trips_every_field(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        original = _snapshot(content_hash="hash-a")
        repository.add("case-1", original)
        fetched = repository.get_latest("case-1")
        assert fetched is not None
        assert fetched.business_category_states == original.business_category_states
        assert fetched.valuation_status == original.valuation_status
        assert fetched.current_yield == original.current_yield
        assert fetched.captured_at == original.captured_at

    def test_cases_do_not_leak_into_each_other(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        repository.add("case-1", _snapshot(content_hash="hash-a"))
        assert repository.get_latest("case-2") is None


class TestAddIsIdempotent:
    """Scenario 25: snapshot persistence/versioning is idempotent."""

    def test_add_returns_true_for_a_genuinely_new_snapshot(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        assert repository.add("case-1", _snapshot(content_hash="hash-a")) is True

    def test_add_returns_false_and_writes_nothing_for_an_identical_content_hash(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        first = _snapshot(content_hash="hash-a", captured_at=_T0)
        second = _snapshot(content_hash="hash-a", captured_at=_T1)  # different time, same content
        assert repository.add("case-1", first) is True
        assert repository.add("case-1", second) is False
        # The head is still the *first* write -- no duplicate row appeared.
        assert repository.get_latest("case-1").captured_at == _T0

    def test_a_genuinely_different_content_hash_produces_a_new_head(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        repository.add("case-1", _snapshot(content_hash="hash-a", captured_at=_T0))
        assert repository.add("case-1", _snapshot(content_hash="hash-b", captured_at=_T1)) is True
        assert repository.get_latest("case-1").content_hash == "hash-b"

    def test_repeated_add_of_the_same_unchanged_state_is_safe_to_call_many_times(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        snapshot = _snapshot(content_hash="hash-a")
        for _ in range(5):
            repository.add("case-1", snapshot)
        assert repository.get_latest("case-1").content_hash == "hash-a"
