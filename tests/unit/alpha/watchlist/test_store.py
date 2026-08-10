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


class TestGetByCaseId:
    def test_returns_none_when_absent(self, store):
        assert store.get_by_case_id("no-such-case") is None

    def test_returns_the_entry_when_present(self, store):
        store.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-1", added_at=_NOW))
        found = store.get_by_case_id("case-1")
        assert found is not None
        assert found.ticker == "AMD"
