"""Tests for Atlas Alpha's provisional portfolio data model."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.alpha.portfolio.models import (
    AlphaHolding,
    AlphaPortfolioState,
    AlphaPreferences,
    EntryMode,
)


class TestAlphaHolding:
    def test_normalizes_ticker_to_uppercase_and_stripped(self):
        holding = AlphaHolding(ticker="  nvda ", weight_percent=10)
        assert holding.ticker == "NVDA"

    def test_rejects_blank_ticker(self):
        with pytest.raises(ValueError):
            AlphaHolding(ticker="   ", weight_percent=10)

    def test_rejects_negative_weight(self):
        with pytest.raises(ValueError):
            AlphaHolding(ticker="NVDA", weight_percent=-1)

    def test_rejects_weight_above_100(self):
        with pytest.raises(ValueError):
            AlphaHolding(ticker="NVDA", weight_percent=100.1)

    def test_accepts_weight_of_exactly_100(self):
        holding = AlphaHolding(ticker="NVDA", weight_percent=100)
        assert holding.weight_percent == 100

    def test_rejects_negative_value_absolute(self):
        with pytest.raises(ValueError):
            AlphaHolding(ticker="NVDA", weight_percent=10, value_absolute=-5)

    def test_value_absolute_is_optional(self):
        holding = AlphaHolding(ticker="NVDA", weight_percent=10)
        assert holding.value_absolute is None

    def test_case_id_defaults_to_none(self):
        holding = AlphaHolding(ticker="NVDA", weight_percent=10)
        assert holding.case_id is None

    def test_case_id_is_preserved_when_given(self):
        holding = AlphaHolding(ticker="NVDA", weight_percent=10, case_id="case-1")
        assert holding.case_id == "case-1"

    def test_quantity_price_currency_default_to_none(self):
        holding = AlphaHolding(ticker="NVDA", weight_percent=10)
        assert holding.quantity is None
        assert holding.price is None
        assert holding.currency is None

    def test_quantity_price_currency_are_preserved_when_given(self):
        holding = AlphaHolding(
            ticker="NVDA", weight_percent=10, quantity=5, price=120.0, currency="usd"
        )
        assert holding.quantity == 5
        assert holding.price == 120.0
        assert holding.currency == "USD"

    def test_rejects_zero_or_negative_quantity(self):
        with pytest.raises(ValueError):
            AlphaHolding(ticker="NVDA", weight_percent=10, quantity=0)

    def test_rejects_zero_or_negative_price(self):
        with pytest.raises(ValueError):
            AlphaHolding(ticker="NVDA", weight_percent=10, price=-1.0)


class TestAlphaPortfolioStateHasAbsoluteValues:
    def _state(self, holdings, cash_value_absolute) -> AlphaPortfolioState:
        now = datetime(2026, 8, 5, tzinfo=timezone.utc)
        return AlphaPortfolioState(
            established_at=now,
            updated_at=now,
            entry_mode=EntryMode.IMPORTED,
            holdings=holdings,
            cash_value_absolute=cash_value_absolute,
        )

    def test_true_when_every_holding_and_cash_have_a_value(self):
        state = self._state(
            (AlphaHolding(ticker="NVDA", weight_percent=50, value_absolute=100.0),),
            cash_value_absolute=10.0,
        )
        assert state.has_absolute_values is True

    def test_false_when_a_holding_is_missing_a_value(self):
        state = self._state(
            (AlphaHolding(ticker="NVDA", weight_percent=50),),
            cash_value_absolute=10.0,
        )
        assert state.has_absolute_values is False

    def test_false_when_cash_value_is_missing(self):
        state = self._state(
            (AlphaHolding(ticker="NVDA", weight_percent=50, value_absolute=100.0),),
            cash_value_absolute=None,
        )
        assert state.has_absolute_values is False


class TestAlphaPortfolioStateHoldingsHaveAbsoluteValues:
    """Sprint 11 Phase 2: a display-only, cash-independent counterpart to
    `has_absolute_values` -- a real import with real holding values but
    no reported cash line must still be able to show a real total."""

    def _state(self, holdings, cash_value_absolute=None) -> AlphaPortfolioState:
        now = datetime(2026, 8, 5, tzinfo=timezone.utc)
        return AlphaPortfolioState(
            established_at=now,
            updated_at=now,
            entry_mode=EntryMode.IMPORTED,
            holdings=holdings,
            cash_value_absolute=cash_value_absolute,
        )

    def test_true_when_every_holding_has_a_value_even_with_no_cash_reported(self):
        state = self._state(
            (AlphaHolding(ticker="NVDA", weight_percent=50, value_absolute=100.0),),
            cash_value_absolute=None,
        )
        assert state.holdings_have_absolute_values is True
        # has_absolute_values (trade-mode gating) is deliberately unaffected.
        assert state.has_absolute_values is False

    def test_true_when_cash_is_also_reported(self):
        state = self._state(
            (AlphaHolding(ticker="NVDA", weight_percent=50, value_absolute=100.0),),
            cash_value_absolute=10.0,
        )
        assert state.holdings_have_absolute_values is True

    def test_false_when_a_holding_is_missing_a_value(self):
        state = self._state((AlphaHolding(ticker="NVDA", weight_percent=50),))
        assert state.holdings_have_absolute_values is False

    def test_true_with_no_holdings_at_all(self):
        state = self._state(())
        assert state.holdings_have_absolute_values is True


class TestAlphaPreferencesAreOptional:
    def test_defaults_to_no_notes(self):
        assert AlphaPreferences().notes is None
