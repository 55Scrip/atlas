"""`AlphaVantageQuotaTracker` tests (Internal Alpha Stabilization 1,
MSFT price root cause fix). Real in-memory SQLite throughout, matching
this package's own established real-harness testing discipline (see
`test_repository.py`).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.quota_table import alpha_vantage_daily_call_count_table


@pytest.fixture
def engine() -> Engine:
    return create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False})


class TestAlphaVantageQuotaTracker:
    def test_starts_at_zero_used_and_full_remaining(self, engine):
        tracker = AlphaVantageQuotaTracker(engine, daily_limit=25)
        assert tracker.calls_used_today() == 0
        assert tracker.remaining_today() == 25
        assert tracker.has_budget() is True

    def test_record_call_increments_used_and_decrements_remaining(self, engine):
        tracker = AlphaVantageQuotaTracker(engine, daily_limit=25)
        tracker.record_call()
        tracker.record_call()
        assert tracker.calls_used_today() == 2
        assert tracker.remaining_today() == 23

    def test_has_budget_false_once_daily_limit_reached(self, engine):
        tracker = AlphaVantageQuotaTracker(engine, daily_limit=2)
        tracker.record_call()
        tracker.record_call()
        assert tracker.calls_used_today() == 2
        assert tracker.remaining_today() == 0
        assert tracker.has_budget() is False

    def test_remaining_today_never_goes_negative_past_the_limit(self, engine):
        """A full company enrichment can cost more than one call in a
        single burst -- `record_call` must never be blocked by the
        limit itself (that is `has_budget`'s job, checked by the
        caller beforehand), so an over-count must still clamp to zero,
        never a negative "remaining"."""
        tracker = AlphaVantageQuotaTracker(engine, daily_limit=1)
        tracker.record_call()
        tracker.record_call()
        tracker.record_call()
        assert tracker.calls_used_today() == 3
        assert tracker.remaining_today() == 0

    def test_persists_across_a_fresh_tracker_instance_on_the_same_engine(self, engine):
        """Simulates a server restart: a brand-new `AlphaVantageQuotaTracker`
        constructed on the same underlying engine must see the same
        count -- the real number lives in the table, not in the
        instance."""
        first = AlphaVantageQuotaTracker(engine, daily_limit=25)
        first.record_call()
        first.record_call()
        first.record_call()

        second = AlphaVantageQuotaTracker(engine, daily_limit=25)
        assert second.calls_used_today() == 3
        assert second.remaining_today() == 22

    def test_two_tracker_instances_share_the_same_running_count(self, engine):
        """Two instances (e.g. one built per-request) on the same
        engine must never disagree -- the table, keyed by date, is the
        single source of truth."""
        a = AlphaVantageQuotaTracker(engine, daily_limit=25)
        b = AlphaVantageQuotaTracker(engine, daily_limit=25)
        a.record_call()
        b.record_call()
        assert a.calls_used_today() == 2
        assert b.calls_used_today() == 2

    def test_a_call_recorded_on_a_different_date_does_not_count_toward_today(self, engine):
        """Date-keyed rollover: a row for yesterday must never inflate
        or deflate today's count -- proven by writing directly into the
        table for a different `call_date`, bypassing the tracker's own
        (always-"today") `record_call`."""
        tracker = AlphaVantageQuotaTracker(engine, daily_limit=25)
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        with engine.begin() as connection:
            connection.execute(
                alpha_vantage_daily_call_count_table.insert().values(call_date=yesterday, call_count=25)
            )
        assert tracker.calls_used_today() == 0
        assert tracker.remaining_today() == 25
        assert tracker.has_budget() is True

    def test_default_daily_limit_matches_the_confirmed_free_tier_ceiling(self, engine):
        from atlas.alpha.business_data_refresh.quota import ALPHA_VANTAGE_FREE_TIER_DAILY_LIMIT

        assert ALPHA_VANTAGE_FREE_TIER_DAILY_LIMIT == 25
        tracker = AlphaVantageQuotaTracker(engine)
        assert tracker.remaining_today() == 25
