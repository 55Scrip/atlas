"""Tests for `atlas.alpha.portfolio.store.AlphaPortfolioStore`."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.portfolio.models import (
    AlphaHolding,
    AlphaPortfolioState,
    AlphaPreferences,
    EntryMode,
    ReconciliationStatus,
)
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table

_NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


@pytest.fixture
def store() -> AlphaPortfolioStore:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_alpha_portfolio_state_table(engine)
    return AlphaPortfolioStore(engine)


class TestAlphaPortfolioStore:
    def test_get_returns_none_when_nothing_established(self, store):
        assert store.get() is None

    def test_replace_then_get_round_trips_a_full_state(self, store):
        state = AlphaPortfolioState(
            established_at=_NOW,
            updated_at=_NOW,
            entry_mode=EntryMode.IMPORTED,
            holdings=(AlphaHolding(ticker="NVDA", weight_percent=60, value_absolute=600.0),),
            cash_weight_percent=40,
            cash_value_absolute=400.0,
            objective="Grow capital",
            horizon="Long",
            preferences=AlphaPreferences(notes="No tobacco"),
        )

        store.replace(state)
        fetched = store.get()

        assert fetched.entry_mode == EntryMode.IMPORTED
        assert fetched.holdings == (AlphaHolding(ticker="NVDA", weight_percent=60, value_absolute=600.0),)
        assert fetched.cash_weight_percent == 40
        assert fetched.objective == "Grow capital"
        assert fetched.preferences.notes == "No tobacco"

    def test_replace_overwrites_the_singleton_row(self, store):
        first = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.FROM_SCRATCH,
            objective="A", horizon="Short",
        )
        second = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.FROM_SCRATCH,
            objective="B", horizon="Long",
        )

        store.replace(first)
        store.replace(second)
        fetched = store.get()

        assert fetched.objective == "B"

    def test_empty_holdings_round_trip(self, store):
        state = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.FROM_SCRATCH,
            objective="Grow capital", horizon="Long",
        )
        store.replace(state)
        fetched = store.get()
        assert fetched.holdings == ()

    def test_holding_case_id_round_trips(self, store):
        state = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED,
            holdings=(AlphaHolding(ticker="NVDA", weight_percent=100, case_id="case-1"),),
        )
        store.replace(state)
        fetched = store.get()
        assert fetched.holdings[0].case_id == "case-1"

    def test_holding_case_id_defaults_to_none_when_absent(self, store):
        state = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED,
            holdings=(AlphaHolding(ticker="NVDA", weight_percent=100),),
        )
        store.replace(state)
        fetched = store.get()
        assert fetched.holdings[0].case_id is None

    def test_holding_reconciliation_status_round_trips(self, store):
        # Regression: a trade-applied holding's reconciliation status was
        # correctly set in-memory but silently lost on the next read,
        # because the JSON blob never carried it -- found during Alpha
        # Sprint 1B manual verification, not by the unit tests that only
        # checked an endpoint's direct in-memory response.
        state = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED,
            holdings=(
                AlphaHolding(
                    ticker="NVDA",
                    weight_percent=100,
                    reconciliation_status=ReconciliationStatus.UPDATED,
                ),
            ),
        )
        store.replace(state)
        fetched = store.get()
        assert fetched.holdings[0].reconciliation_status == ReconciliationStatus.UPDATED

    def test_holding_reconciliation_status_defaults_to_none_when_absent(self, store):
        state = AlphaPortfolioState(
            established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED,
            holdings=(AlphaHolding(ticker="NVDA", weight_percent=100),),
        )
        store.replace(state)
        fetched = store.get()
        assert fetched.holdings[0].reconciliation_status == ReconciliationStatus.NONE
