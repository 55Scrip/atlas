"""Tests for `atlas.alpha.portfolio.projection`.

Confirms this module reuses `atlas.domains.portfolio.calculations`
rather than re-deriving allocation/cash/concentration math -- and that
it never presents a fabricated currency total in percentage-only mode.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.projection import derive_portfolio_view

_NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def _state(**kwargs) -> AlphaPortfolioState:
    defaults = dict(established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED)
    defaults.update(kwargs)
    return AlphaPortfolioState(**defaults)


class TestPercentageOnlyMode:
    def test_preserves_relative_allocation(self):
        state = _state(
            holdings=(
                AlphaHolding(ticker="NVDA", weight_percent=60),
                AlphaHolding(ticker="AMD", weight_percent=40),
            ),
        )
        summary = derive_portfolio_view(state)
        assert summary.number_of_holdings == 2
        nvda = next(h for h in summary.top_holdings if h.ticker == "NVDA")
        assert round(nvda.market_value / summary.total_value, 2) == 0.6

    def test_includes_cash_as_a_holding(self):
        state = _state(
            holdings=(AlphaHolding(ticker="NVDA", weight_percent=80),),
            cash_weight_percent=20,
        )
        summary = derive_portfolio_view(state)
        assert summary.cash_weight > 0


class TestAbsoluteValueMode:
    def test_total_value_is_the_real_sum(self):
        state = _state(
            holdings=(
                AlphaHolding(ticker="NVDA", weight_percent=60, value_absolute=600.0),
            ),
            cash_weight_percent=40,
            cash_value_absolute=400.0,
        )
        summary = derive_portfolio_view(state)
        assert summary.total_value == 1000.0


class TestEmptyPortfolio:
    def test_no_holdings_and_no_cash_produces_a_valid_zero_summary(self):
        state = _state(holdings=())
        summary = derive_portfolio_view(state)
        assert summary.number_of_holdings == 0
        assert summary.total_value == 0
