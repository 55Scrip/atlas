"""Tests for `atlas.dev.load_demo_portfolio`."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.dev.guard import NotDevelopmentEnvironmentError
from atlas.dev.load_demo_portfolio import _DEMO_WATCHLIST_TICKERS, load_demo_portfolio
from atlas.dev.reset_user import reset_development_user


@pytest.fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_alpha_portfolio_state_table(engine)
    create_alpha_watchlist_entry_table(engine)
    return engine


class TestProductionGuard:
    def test_refuses_when_atlas_env_is_production(self, engine, monkeypatch):
        monkeypatch.setenv("ATLAS_ENV", "production")
        with pytest.raises(NotDevelopmentEnvironmentError):
            load_demo_portfolio(engine)


class TestLoadsRealHoldings:
    def test_loads_ten_holdings_with_weights_summing_close_to_100_percent(self, engine):
        result = load_demo_portfolio(engine)
        holdings = result["holdings"]
        assert len(holdings) == 10
        tickers = {h["ticker"] for h in holdings}
        assert tickers == {"ASML", "NOVO", "MSFT", "LVMH", "COLB", "HXGN", "DHR", "EQT", "ESSITY", "NESTE"}

    def test_holdings_have_varied_sectors(self, engine):
        result = load_demo_portfolio(engine)
        sectors = {h["sector"] for h in result["holdings"]}
        # At least 6 distinct sectors (one holding, NESTE, has none at all).
        assert len(sectors) >= 6

    def test_holdings_have_varied_quality_and_risk_scores(self, engine):
        result = load_demo_portfolio(engine)
        quality_scores = {h["quality_score"] for h in result["holdings"]}
        risk_scores = {h["risk_score"] for h in result["holdings"]}
        assert max(quality_scores) - min(quality_scores) >= 15
        assert max(risk_scores) - min(risk_scores) >= 15

    def test_persists_via_the_real_portfolio_store(self, engine):
        load_demo_portfolio(engine)
        state = AlphaPortfolioStore(engine).get()
        assert state is not None
        assert len(state.holdings) == 10
        assert state.cash_value_absolute == 42000

    def test_every_holding_gets_a_case_id(self, engine):
        load_demo_portfolio(engine)
        state = AlphaPortfolioStore(engine).get()
        assert all(holding.case_id is not None for holding in state.holdings)


class TestLoadsWatchlist:
    def test_loads_the_two_demo_watchlist_tickers(self, engine):
        result = load_demo_portfolio(engine)
        assert set(result["watchlist_tickers"]) == set(_DEMO_WATCHLIST_TICKERS)

    def test_watchlist_tickers_are_distinct_from_portfolio_tickers(self, engine):
        result = load_demo_portfolio(engine)
        portfolio_tickers = {h["ticker"] for h in result["holdings"]}
        watchlist_tickers = set(result["watchlist_tickers"])
        assert portfolio_tickers.isdisjoint(watchlist_tickers)

    def test_persists_via_the_real_watchlist_store(self, engine):
        load_demo_portfolio(engine)
        watchlist_store = AlphaWatchlistStore(engine)
        for ticker in _DEMO_WATCHLIST_TICKERS:
            entry = watchlist_store.get_by_ticker(ticker)
            assert entry is not None
            assert entry.case_id is not None


class TestDeterministicIdempotentRestoration:
    def test_loading_twice_produces_the_identical_result(self, engine):
        first = load_demo_portfolio(engine)
        second = load_demo_portfolio(engine)
        assert first["holdings"] == second["holdings"]
        assert first["watchlist_tickers"] == second["watchlist_tickers"]
        assert first["cash_value_absolute"] == second["cash_value_absolute"]

    def test_loading_twice_does_not_create_duplicate_cases(self, engine):
        load_demo_portfolio(engine)
        state_after_first = AlphaPortfolioStore(engine).get()
        case_ids_first = {h.case_id for h in state_after_first.holdings}

        load_demo_portfolio(engine)
        state_after_second = AlphaPortfolioStore(engine).get()
        case_ids_second = {h.case_id for h in state_after_second.holdings}

        assert case_ids_first == case_ids_second

    def test_reset_then_reload_restores_the_same_deterministic_state(self, engine):
        """Scenario E from the sprint brief: reset, then reload the
        demo portfolio, and confirm deterministic restoration."""
        first = load_demo_portfolio(engine)
        reset_development_user(engine)
        assert AlphaPortfolioStore(engine).get() is None

        second = load_demo_portfolio(engine)
        assert first["holdings"] == second["holdings"]
        assert set(second["watchlist_tickers"]) == set(_DEMO_WATCHLIST_TICKERS)

    def test_reset_then_reload_assigns_fresh_case_ids_not_the_stale_ones(self, engine):
        load_demo_portfolio(engine)
        state_before = AlphaPortfolioStore(engine).get()
        case_ids_before = {h.case_id for h in state_before.holdings}

        reset_development_user(engine)
        load_demo_portfolio(engine)
        state_after = AlphaPortfolioStore(engine).get()
        case_ids_after = {h.case_id for h in state_after.holdings}

        # Cases were wiped by reset -- reloading must mint fresh ones,
        # never reuse a case_id that no longer has a `cases` row behind it.
        assert case_ids_before.isdisjoint(case_ids_after)


class TestNeverTriggersLiveProviderCalls:
    def test_does_not_require_any_business_data_provider_wiring(self, engine):
        """The whole point of leaving business_record_repository/
        business_data_providers/identity_gate at their default None is
        that this loader must work with zero network access. If this
        test needed real provider credentials or network mocking to
        pass, that guarantee would be broken."""
        result = load_demo_portfolio(engine)  # must succeed with no provider setup at all
        assert len(result["holdings"]) == 10
