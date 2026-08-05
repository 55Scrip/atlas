"""Derives a read-only portfolio view from Alpha's provisional state.

Reuses `atlas.domains.portfolio.calculations` — the existing, unmodified
Portfolio Domain calculation engine — rather than re-deriving allocation,
concentration, or cash math here. This module's own job is narrow:
convert `AlphaPortfolioState` into the `atlas.shared.Portfolio`/`Holding`
shape that engine already expects, honestly reflecting what Alpha
actually knows.
"""
from __future__ import annotations

from atlas.alpha.portfolio.models import AlphaPortfolioState
from atlas.domains.portfolio.calculations import portfolio_summary
from atlas.domains.portfolio.models import PortfolioSummary
from atlas.shared import Holding, Portfolio

_CASH_TICKER = "CASH"


def derive_portfolio_view(state: AlphaPortfolioState) -> PortfolioSummary:
    """Return the Portfolio Domain's own summary for the given state.

    When `state.has_absolute_values` is True, each holding's real
    `value_absolute` is used as `market_value`, so the resulting
    `total_value`/`cash_value` are meaningful currency figures. When it
    is False, `weight_percent` is used as a stand-in `market_value` —
    the same deterministic technique `atlas.adapters.portfolio` already
    uses for the legacy CLI format — which preserves relative allocation
    percentages exactly but produces no meaningful currency total.
    Callers MUST check `state.has_absolute_values` (surfaced as
    `hasAbsoluteValues` in `api/schemas.py`) before presenting
    `total_value`/`cash_value` as real currency.
    """
    holdings = tuple(
        Holding(
            company_id=holding.ticker,
            ticker=holding.ticker,
            market_value=(
                holding.value_absolute
                if state.has_absolute_values and holding.value_absolute is not None
                else holding.weight_percent
            ),
            weight=holding.weight_percent / 100,
        )
        for holding in state.holdings
    )

    if state.cash_weight_percent is not None or state.cash_value_absolute is not None:
        cash_value = (
            state.cash_value_absolute
            if state.has_absolute_values and state.cash_value_absolute is not None
            else (state.cash_weight_percent or 0.0)
        )
        holdings = holdings + (
            Holding(
                company_id=_CASH_TICKER,
                ticker=_CASH_TICKER,
                market_value=cash_value,
                weight=(state.cash_weight_percent or 0.0) / 100,
                asset_type="cash",
            ),
        )

    portfolio = Portfolio(id="alpha-portfolio", name="Alpha Portfolio", holdings=holdings)
    return portfolio_summary(portfolio)
