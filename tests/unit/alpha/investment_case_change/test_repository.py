"""`SqlAlchemyInvestmentCaseSnapshotRepository` tests (Investment Case
Monitoring & Change Intelligence v1; extended for History v1's own
`get_history`/persisted-`ChangeIntelligence` behavior). Real in-memory
SQLite throughout, matching `business_data_refresh`'s own established
real-harness testing discipline.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_change.table import create_investment_case_snapshot_table
from atlas.analysis_engine.investment_case_change import (
    AnalyticalSnapshot,
    ChangeCategory,
    ChangeDirection,
    ChangeFinding,
    ChangeIntelligence,
    ThesisImpact,
    compare_snapshots,
)

_T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
_T1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
_T2 = datetime(2026, 3, 1, tzinfo=timezone.utc)


def _snapshot(
    *,
    content_hash: str,
    captured_at: datetime = _T0,
    current_yield: float | None = 0.03,
    growth_status: str = "moderate",
    atlas_thesis_narrative: str | None = "The case is supported by growth.",
    atlas_thesis_posture: str | None = "strengths_only",
) -> AnalyticalSnapshot:
    return AnalyticalSnapshot(
        business_category_states=(("growth", growth_status, "business_finding:growth"),),
        risk_category_states=(),
        valuation_status="fairly_valued",
        valuation_finding_id="valuation_finding:fcf_yield_relative",
        current_yield=current_yield,
        strength_kinds=(),
        risk_highlight_kinds=(),
        open_question_origins=(),
        atlas_thesis_narrative=atlas_thesis_narrative,
        atlas_thesis_posture=atlas_thesis_posture,
        content_hash=content_hash,
        captured_at=captured_at,
    )


def _baseline_change_intelligence(captured_at: datetime = _T0) -> ChangeIntelligence:
    return compare_snapshots(None, _snapshot(content_hash="unused", captured_at=captured_at))


def _real_change(previous: AnalyticalSnapshot, current: AnalyticalSnapshot) -> ChangeIntelligence:
    return compare_snapshots(previous, current)


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
        first = _snapshot(content_hash="hash-a", captured_at=_T0)
        repository.add("case-1", first, _baseline_change_intelligence(_T0))
        second = _snapshot(content_hash="hash-b", captured_at=_T1)
        repository.add("case-1", second, _real_change(first, second))
        latest = repository.get_latest("case-1")
        assert latest is not None
        assert latest.content_hash == "hash-b"

    def test_round_trips_every_field(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        original = _snapshot(content_hash="hash-a")
        repository.add("case-1", original, _baseline_change_intelligence())
        fetched = repository.get_latest("case-1")
        assert fetched is not None
        assert fetched.business_category_states == original.business_category_states
        assert fetched.valuation_status == original.valuation_status
        assert fetched.current_yield == original.current_yield
        assert fetched.captured_at == original.captured_at
        assert fetched.atlas_thesis_narrative == original.atlas_thesis_narrative
        assert fetched.atlas_thesis_posture == original.atlas_thesis_posture

    def test_cases_do_not_leak_into_each_other(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        repository.add("case-1", _snapshot(content_hash="hash-a"), _baseline_change_intelligence())
        assert repository.get_latest("case-2") is None


class TestAddIsIdempotent:
    """Scenario 25: snapshot persistence/versioning is idempotent."""

    def test_add_returns_true_for_a_genuinely_new_snapshot(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        assert repository.add("case-1", _snapshot(content_hash="hash-a"), _baseline_change_intelligence()) is True

    def test_add_returns_false_and_writes_nothing_for_an_identical_content_hash(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        first = _snapshot(content_hash="hash-a", captured_at=_T0)
        second = _snapshot(content_hash="hash-a", captured_at=_T1)  # different time, same content
        assert repository.add("case-1", first, _baseline_change_intelligence(_T0)) is True
        assert repository.add("case-1", second, _real_change(first, second)) is False
        # The head is still the *first* write -- no duplicate row appeared.
        assert repository.get_latest("case-1").captured_at == _T0

    def test_a_genuinely_different_content_hash_produces_a_new_head(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        first = _snapshot(content_hash="hash-a", captured_at=_T0)
        second = _snapshot(content_hash="hash-b", captured_at=_T1)
        repository.add("case-1", first, _baseline_change_intelligence(_T0))
        assert repository.add("case-1", second, _real_change(first, second)) is True
        assert repository.get_latest("case-1").content_hash == "hash-b"

    def test_repeated_add_of_the_same_unchanged_state_is_safe_to_call_many_times(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        snapshot = _snapshot(content_hash="hash-a")
        change_intelligence = _baseline_change_intelligence()
        for _ in range(5):
            repository.add("case-1", snapshot, change_intelligence)
        assert repository.get_latest("case-1").content_hash == "hash-a"


class TestGetHistory:
    """History v1: `get_history` reads persisted state/transitions only
    -- never writes, never recomputes a real (non-baseline) comparison."""

    def test_no_snapshots_returns_an_empty_history(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        assert repository.get_history("case-1") == ()

    def test_one_snapshot_is_a_single_baseline_entry(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        snapshot = _snapshot(content_hash="hash-a", captured_at=_T0)
        repository.add("case-1", snapshot, _baseline_change_intelligence(_T0))
        history = repository.get_history("case-1")
        assert len(history) == 1
        fetched_snapshot, change_intelligence = history[0]
        assert fetched_snapshot.content_hash == "hash-a"
        assert change_intelligence.is_baseline is True
        assert change_intelligence.changes == ()
        assert change_intelligence.previous_captured_at is None

    def test_two_snapshots_produce_a_baseline_and_one_transition_entry(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        first = _snapshot(content_hash="hash-a", captured_at=_T0, growth_status="strong")
        second = _snapshot(content_hash="hash-b", captured_at=_T1, growth_status="moderate")
        repository.add("case-1", first, _baseline_change_intelligence(_T0))
        repository.add("case-1", second, _real_change(first, second))

        history = repository.get_history("case-1")
        assert len(history) == 2
        baseline_snapshot, baseline_ci = history[0]
        assert baseline_ci.is_baseline is True
        second_snapshot, second_ci = history[1]
        assert second_ci.is_baseline is False
        assert second_ci.previous_captured_at == _T0
        assert second_ci.current_captured_at == _T1
        assert len(second_ci.changes) == 1
        assert second_ci.changes[0].category is ChangeCategory.GROWTH_CHANGED
        assert second_ci.changes[0].direction is ChangeDirection.NEGATIVE

    def test_three_snapshots_are_returned_oldest_first(self, engine):
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        s0 = _snapshot(content_hash="hash-a", captured_at=_T0, growth_status="strong")
        s1 = _snapshot(content_hash="hash-b", captured_at=_T1, growth_status="moderate")
        s2 = _snapshot(content_hash="hash-c", captured_at=_T2, growth_status="strong")
        repository.add("case-1", s0, _baseline_change_intelligence(_T0))
        repository.add("case-1", s1, _real_change(s0, s1))
        repository.add("case-1", s2, _real_change(s1, s2))

        history = repository.get_history("case-1")
        assert [snap.captured_at for snap, _ in history] == [_T0, _T1, _T2]

    def test_history_persistence_never_writes(self, engine):
        """Scenario 27: reading history never mutates snapshot persistence."""
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        snapshot = _snapshot(content_hash="hash-a", captured_at=_T0)
        repository.add("case-1", snapshot, _baseline_change_intelligence(_T0))
        before = repository.get_history("case-1")
        for _ in range(5):
            repository.get_history("case-1")
        after = repository.get_history("case-1")
        assert before == after
        assert len(after) == 1

    def test_a_row_with_no_persisted_change_intelligence_is_reported_honestly(self, engine):
        """Backward compatibility: a row written with `change_intelligence_json`
        NULL (either genuinely absent, or predating the column) must
        never be silently recomputed -- it reports "unavailable"."""
        from sqlalchemy import insert

        from atlas.alpha.investment_case_change.table import investment_case_snapshot_table

        with engine.begin() as connection:
            connection.execute(
                insert(investment_case_snapshot_table).values(
                    id="case-1:2026-01-01T00:00:00+00:00",
                    case_id="case-1",
                    captured_at=_T0.isoformat(),
                    content_hash="hash-legacy",
                    current_yield=None,
                    snapshot_json='{"business_category_states": [], "risk_category_states": [], "valuation_status": "insufficient_input", "valuation_finding_id": "valuation_finding:fcf_yield_relative", "strength_kinds": [], "risk_highlight_kinds": [], "open_question_origins": []}',
                    change_intelligence_json=None,
                )
            )
            connection.execute(
                insert(investment_case_snapshot_table).values(
                    id="case-1:2026-02-01T00:00:00+00:00",
                    case_id="case-1",
                    captured_at=_T1.isoformat(),
                    content_hash="hash-legacy-2",
                    current_yield=None,
                    snapshot_json='{"business_category_states": [], "risk_category_states": [], "valuation_status": "insufficient_input", "valuation_finding_id": "valuation_finding:fcf_yield_relative", "strength_kinds": [], "risk_highlight_kinds": [], "open_question_origins": []}',
                    change_intelligence_json=None,
                )
            )
        repository = SqlAlchemyInvestmentCaseSnapshotRepository(engine)
        history = repository.get_history("case-1")
        assert len(history) == 2
        # Old rows predate the atlas_thesis_narrative/posture fields too.
        assert history[0][0].atlas_thesis_narrative is None
        assert history[0][0].atlas_thesis_posture is None
        # Second row predates change_intelligence_json -- honest fallback.
        _, second_ci = history[1]
        assert second_ci.is_baseline is False
        assert second_ci.changes == ()
        assert "not available" in second_ci.summary_narrative.lower()
