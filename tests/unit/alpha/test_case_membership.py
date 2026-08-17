"""Tests for `atlas.alpha.case_membership.resolve_case_id_for_ticker`
(Ticker -> Existing Case Resolution Sprint).

`known_cases` (the module's pre-existing function) is exercised only
indirectly elsewhere (via `daily_brief`/`investment_case_history`);
this file is this module's first direct test coverage, added alongside
its new complementary function.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table

_NOW = datetime(2026, 8, 18, tzinfo=timezone.utc)


def _new_engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_alpha_portfolio_state_table(engine)
    create_alpha_watchlist_entry_table(engine)
    return engine


@pytest.fixture
def engine():
    return _new_engine()


@pytest.fixture
def portfolio_store(engine) -> AlphaPortfolioStore:
    return AlphaPortfolioStore(engine)


@pytest.fixture
def watchlist_store(engine) -> AlphaWatchlistStore:
    return AlphaWatchlistStore(engine)


class TestNoExistingCase:
    def test_returns_none_for_a_ticker_never_seen_anywhere(self, portfolio_store, watchlist_store):
        assert resolve_case_id_for_ticker("AMD", portfolio_store, watchlist_store) is None

    def test_returns_none_when_portfolio_store_is_omitted(self, watchlist_store):
        assert resolve_case_id_for_ticker("AMD", None, watchlist_store) is None


class TestActiveWatchlistEntry:
    def test_resolves_the_case_id_of_an_active_entry(self, portfolio_store, watchlist_store):
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        assert resolve_case_id_for_ticker("AMD", portfolio_store, watchlist_store) == "case-1"


class TestRemovedWatchlistHistory:
    def test_resolves_the_case_id_of_a_removed_entry(self, portfolio_store, watchlist_store):
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        watchlist_store.remove("AMD", _NOW)
        assert resolve_case_id_for_ticker("AMD", portfolio_store, watchlist_store) == "case-1"

    def test_is_the_lowest_priority_source(self, portfolio_store, watchlist_store):
        """The exact scenario this function's own docstring names:
        a ticker with stale, removed Watchlist history pointing at one
        Case, and a *current* Portfolio holding pointing at a
        different one -- the current holding must win, never the
        stale history, or the same ticker would silently split across
        two Cases at once."""
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="stale-case", added_at=_NOW))
        watchlist_store.remove("AMD", _NOW)
        portfolio_store.replace(
            AlphaPortfolioState(
                established_at=_NOW,
                updated_at=_NOW,
                entry_mode=EntryMode.IMPORTED,
                holdings=(AlphaHolding(ticker="AMD", weight_percent=10.0, case_id="current-case"),),
            )
        )
        assert resolve_case_id_for_ticker("AMD", portfolio_store, watchlist_store) == "current-case"


class TestPortfolioPriority:
    def test_current_portfolio_holding_wins_over_active_watchlist_entry_for_a_different_case(
        self, portfolio_store, watchlist_store
    ):
        """Not expected to occur under this codebase's own cross-context
        reuse guarantees (Watchlist add already reuses a Portfolio
        Case for the same ticker), but Portfolio is still checked first
        defensively, matching this function's documented priority
        order exactly."""
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="watchlist-case", added_at=_NOW))
        portfolio_store.replace(
            AlphaPortfolioState(
                established_at=_NOW,
                updated_at=_NOW,
                entry_mode=EntryMode.IMPORTED,
                holdings=(AlphaHolding(ticker="AMD", weight_percent=10.0, case_id="portfolio-case"),),
            )
        )
        assert resolve_case_id_for_ticker("AMD", portfolio_store, watchlist_store) == "portfolio-case"


class TestNormalization:
    def test_lowercase_input_resolves_the_same_as_uppercase(self, portfolio_store, watchlist_store):
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        assert resolve_case_id_for_ticker("amd", portfolio_store, watchlist_store) == "case-1"

    def test_whitespace_is_stripped(self, portfolio_store, watchlist_store):
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        assert resolve_case_id_for_ticker("  amd  ", portfolio_store, watchlist_store) == "case-1"


class TestUnrelatedTickersUnaffected:
    def test_a_second_tickers_history_does_not_leak_into_the_first(self, portfolio_store, watchlist_store):
        watchlist_store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        watchlist_store.add(AlphaWatchlistEntry(ticker="NVDA", case_id="case-2", added_at=_NOW))
        watchlist_store.remove("AMD", _NOW)
        assert resolve_case_id_for_ticker("NVDA", portfolio_store, watchlist_store) == "case-2"
        assert resolve_case_id_for_ticker("AMD", portfolio_store, watchlist_store) == "case-1"
