"""Tests for `atlas.alpha.watchlist.store.AlphaWatchlistStore`."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _new_store() -> AlphaWatchlistStore:
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_alpha_watchlist_entry_table(engine)
    return AlphaWatchlistStore(engine)


@pytest.fixture
def store() -> AlphaWatchlistStore:
    return _new_store()


class TestAddAndList:
    def test_add_then_list_all_returns_it(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        entries = store.list_all()
        assert len(entries) == 1
        assert entries[0].ticker == "AMD"
        assert entries[0].case_id == "case-1"

    def test_empty_store_lists_nothing(self, store):
        assert store.list_all() == ()

    def test_multiple_entries_all_present(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.add(AlphaWatchlistEntry(ticker="NVDA", case_id="case-2", added_at=_NOW))
        assert {e.ticker for e in store.list_all()} == {"AMD", "NVDA"}


class TestGetByTicker:
    def test_returns_none_when_absent(self, store):
        assert store.get_by_ticker("AMD") is None

    def test_returns_the_entry_when_present(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        found = store.get_by_ticker("AMD")
        assert found is not None
        assert found.case_id == "case-1"

    def test_lookup_is_case_insensitive(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        assert store.get_by_ticker("amd") is not None


class TestRemove:
    """`remove` is a soft delete (Ticker -> Existing Case Resolution
    Sprint): the row survives with `removed_at` set, so
    `get_by_ticker`/`list_all` (active-only) stop showing it, exactly
    as before, while `get_by_ticker_including_removed` can still find
    its `case_id`."""

    def test_removes_an_existing_entry(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.remove("AMD", _NOW)
        assert store.get_by_ticker("AMD") is None

    def test_other_entries_remain_after_removal(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.add(AlphaWatchlistEntry(ticker="NVDA", case_id="case-2", added_at=_NOW))
        store.remove("AMD", _NOW)
        assert {e.ticker for e in store.list_all()} == {"NVDA"}

    def test_removing_an_absent_ticker_is_a_no_op(self, store):
        store.remove("AMD", _NOW)
        assert store.list_all() == ()

    def test_removal_is_case_insensitive(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.remove("amd", _NOW)
        assert store.get_by_ticker("AMD") is None

    def test_add_remove_add_again_reactivates_the_same_row(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.remove("AMD", _NOW)
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        found = store.get_by_ticker("AMD")
        assert found is not None
        assert found.case_id == "case-1"

    def test_removed_entry_survives_in_get_by_ticker_including_removed(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.remove("AMD", _NOW)
        found = store.get_by_ticker_including_removed("AMD")
        assert found is not None
        assert found.case_id == "case-1"


class TestGetByTickerIncludingRemoved:
    def test_returns_none_when_never_added(self, store):
        assert store.get_by_ticker_including_removed("AMD") is None

    def test_returns_an_active_entry(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        found = store.get_by_ticker_including_removed("AMD")
        assert found is not None
        assert found.case_id == "case-1"

    def test_case_insensitive(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.remove("AMD", _NOW)
        assert store.get_by_ticker_including_removed("amd") is not None


class TestListAllIncludingRemoved:
    def test_includes_both_active_and_removed_entries(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.add(AlphaWatchlistEntry(ticker="NVDA", case_id="case-2", added_at=_NOW))
        store.remove("AMD", _NOW)
        tickers = {e.ticker for e in store.list_all_including_removed()}
        assert tickers == {"AMD", "NVDA"}


class TestGetByCaseId:
    def test_returns_none_when_absent(self, store):
        assert store.get_by_case_id("no-such-case") is None

    def test_returns_the_entry_when_present(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        found = store.get_by_case_id("case-1")
        assert found is not None
        assert found.ticker == "AMD"

    def test_returns_a_removed_entry_too(self, store):
        """Deliberate: `InvestmentCaseCompositionService._assemble`
        relies on this to keep recovering a Watchlist-only Case's
        ticker after the Watchlist entry has been removed."""
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        store.remove("AMD", _NOW)
        found = store.get_by_case_id("case-1")
        assert found is not None
        assert found.ticker == "AMD"
