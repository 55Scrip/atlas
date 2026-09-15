"""`refresh_prices_with_listed_siblings`: one price refresh of a security
that is one of several listed classes of its issuer refreshes every listed
sibling in the same pass -- one call each, budget reserved up front, paced,
failing closed -- and a security without siblings takes exactly the single
refresh it always did. Real in-memory SQLite repository and quota tracker,
the real `AlphaVantageMarketDataProvider` against a fake fetcher."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.business_data_refresh.price_refresh import (
    PriceRefreshCoordinator,
    refresh_prices_with_listed_siblings,
)
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from tests.unit.alpha.business_data_refresh.test_price_refresh import _snapshot_record

_NOW = datetime(2026, 9, 15, 13, tzinfo=timezone.utc)
_DAY = "2026-09-14"


class _Harness:
    """Two listed classes AAA/AAC of one issuer and a single listing SGL,
    each with a stale stored quote; a fetcher answering GLOBAL_QUOTE per
    symbol and recording every real request."""

    def __init__(self, *, days=None, failing=(), limit=25, used=0):
        engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        create_business_record_table(engine)
        self.repository = SqlAlchemyBusinessRecordRepository(engine)
        for company in ("AAA", "AAC", "SGL"):
            self.repository.add(_snapshot_record(company=company, trading_day=date(2026, 8, 21)))
        self.quota = AlphaVantageQuotaTracker(engine, daily_limit=limit)
        for _ in range(used):
            self.quota.record_call()
        self.coordinator = PriceRefreshCoordinator()
        self.requests: list[str] = []
        self.sleeps: list[float] = []
        self.days = days or {}
        self.failing = set(failing)
        self.provider = AlphaVantageMarketDataProvider(
            self._fetch, api_key="test", on_request=self.quota.record_call, sleeper=self.sleeps.append,
            clock=lambda: 100.0, inter_request_delay_seconds=1.0)

    def _fetch(self, url, headers):
        symbol = url.split("symbol=", 1)[1].split("&", 1)[0]
        self.requests.append(symbol)
        if symbol in self.failing:
            return {}  # no "Global Quote": the provider raises, the refresh reports failure
        return {"Global Quote": {"05. price": "100.00", "07. latest trading day": self.days.get(symbol, _DAY)}}

    def refresh(self, ticker, siblings):
        return refresh_prices_with_listed_siblings(ticker, siblings=siblings, provider=self.provider,
                                                   repository=self.repository, quota=self.quota,
                                                   coordinator=self.coordinator, evaluated_at=_NOW)

    def quote_days(self, *tickers):
        return {t: max(r.period_end for r in self.repository.get_by_company(t)) for t in tickers}


class TestWhoIsCalled:
    def test_a_single_listing_is_one_call(self):
        h = _Harness()
        outcome = h.refresh("SGL", ())
        assert h.requests == ["SGL"]
        assert (outcome.succeeded, outcome.synchronized, outcome.reason) == (True, None, "ok")

    def test_refreshing_one_listed_class_refreshes_its_sibling_once(self):
        h = _Harness()
        outcome = h.refresh("AAA", ("AAC",))
        assert h.requests == ["AAA", "AAC"]
        assert (outcome.succeeded, outcome.synchronized, outcome.reason) == (True, True, "ok")

    def test_refreshing_the_other_class_refreshes_the_first_once(self):
        h = _Harness()
        h.refresh("AAC", ("AAA",))
        assert h.requests == ["AAC", "AAA"]

    def test_no_duplicate_calls_and_the_requested_security_is_never_its_own_sibling(self):
        h = _Harness()
        h.refresh("AAA", ("AAC", "AAC", "AAA", ""))
        assert h.requests == ["AAA", "AAC"]

    def test_a_pass_never_reaches_beyond_the_siblings_it_was_given(self):
        h = _Harness()
        h.refresh("AAA", ("AAC",))
        assert "SGL" not in h.requests

    def test_calls_are_paced_on_the_one_provider_instance(self):
        h = _Harness()
        h.refresh("AAA", ("AAC",))
        assert h.sleeps == [1.0]  # one pause, before the sibling's call

    def test_the_counter_counts_real_calls_only(self):
        h = _Harness()
        h.refresh("AAA", ("AAC",))
        assert h.quota.calls_used_today() == 2


class TestBudget:
    def test_not_enough_budget_for_every_sibling_makes_no_call(self):
        h = _Harness(limit=25, used=24)
        outcome = h.refresh("AAA", ("AAC",))
        assert h.requests == []
        assert (outcome.attempted, outcome.reason) == (False, "quota_insufficient")
        assert h.quota.calls_used_today() == 24
        assert not any(h.coordinator.is_refreshing(t) for t in ("AAA", "AAC"))

    def test_refreshes_already_in_flight_are_counted_against_the_budget(self):
        h = _Harness(limit=25, used=22)
        assert h.coordinator.try_start("SGL")  # one call in flight elsewhere
        assert h.refresh("AAA", ("AAC",)).reason == "ok"  # 3 left, 1 spoken for, 2 needed
        h2 = _Harness(limit=25, used=23)
        assert h2.coordinator.try_start("SGL")
        assert h2.refresh("AAA", ("AAC",)).reason == "quota_insufficient"  # 2 left, 1 spoken for
        assert h2.requests == []

    def test_a_sibling_already_refreshing_claims_nothing(self):
        h = _Harness()
        assert h.coordinator.try_start("AAC")
        outcome = h.refresh("AAA", ("AAC",))
        assert (h.requests, outcome.reason) == ([], "already_refreshing")
        assert not h.coordinator.is_refreshing("AAA")


class TestFailClosed:
    def test_a_failed_sibling_leaves_the_pass_unsynchronized(self):
        h = _Harness(failing={"AAC"})
        outcome = h.refresh("AAA", ("AAC",))
        assert h.requests == ["AAA", "AAC"]
        assert outcome.succeeded  # the requested security did refresh
        assert (outcome.synchronized, outcome.reason) == (False, "listed_sibling_refresh_failed:AAC")
        assert h.quote_days("AAA", "AAC") == {"AAA": date(2026, 9, 14), "AAC": date(2026, 8, 21)}
        assert h.coordinator.has_recently_failed("AAC") and not h.coordinator.is_refreshing("AAC")

    def test_a_failed_first_call_spends_nothing_on_the_siblings(self):
        h = _Harness(failing={"AAA"})
        outcome = h.refresh("AAA", ("AAC",))
        assert h.requests == ["AAA"]
        assert dict(outcome.outcomes)["AAC"].reason == "not_attempted_after_AAA_failed"
        assert not h.coordinator.is_refreshing("AAC") and not h.coordinator.has_recently_failed("AAC")

    def test_siblings_answering_different_trading_days_are_reported_unsynchronized(self):
        h = _Harness(days={"AAA": "2026-09-14", "AAC": "2026-09-11"})
        outcome = h.refresh("AAA", ("AAC",))
        assert (outcome.succeeded, outcome.synchronized, outcome.reason) == (True, False, "listed_siblings_not_synchronized")

    def test_an_unexpected_error_releases_every_claim(self, monkeypatch):
        import atlas.alpha.business_data_refresh.price_refresh as module

        h = _Harness()

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(module, "_refresh_claimed", boom)
        with pytest.raises(RuntimeError):
            h.refresh("AAA", ("AAC",))
        assert not any(h.coordinator.is_refreshing(t) for t in ("AAA", "AAC"))
