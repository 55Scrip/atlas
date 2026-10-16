"""A portfolio says what its amounts are denominated in, or says nothing.

Sprint 69 drove the real UI and found the Portfolio page rendering
`$2,543,747` for a portfolio whose every holding is stored in SEK. The
figures were right; the unit was wrong, because the display layer had one
hardcoded `Intl.NumberFormat(..., {currency: "USD"})` and the API never told
it otherwise. These tests cover the half of that fix the backend owns:
establishing the denomination, and refusing to establish one when it cannot.

`None` is a first-class answer here. The display contract is that an amount
with no established currency renders without a symbol -- so a wrong label can
never be produced from a confident-looking default.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.alpha.portfolio.api.schemas import PortfolioView
from atlas.alpha.portfolio.models import (
    AlphaHolding,
    AlphaPortfolioState,
    EntryMode,
)
from atlas.alpha.portfolio.projection import derive_portfolio_view

_NOW = datetime(2026, 10, 16, tzinfo=timezone.utc)


def state(*holdings: AlphaHolding, cash_value: float | None = None,
          cash_weight: float | None = None) -> AlphaPortfolioState:
    return AlphaPortfolioState(
        established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.IMPORTED,
        holdings=holdings, cash_value_absolute=cash_value,
        cash_weight_percent=cash_weight,
    )


def valued(ticker: str, weight: float, value: float, currency: str | None) -> AlphaHolding:
    return AlphaHolding(ticker=ticker, weight_percent=weight, value_absolute=value,
                        currency=currency)


class TestReportingCurrency:
    @pytest.mark.parametrize("code", ["SEK", "USD", "EUR", "DKK", "NOK", "GBP"])
    def test_one_currency_across_valued_holdings_is_the_portfolio_currency(self, code):
        s = state(valued("A", 60.0, 600.0, code), valued("B", 40.0, 400.0, code))

        assert s.reporting_currency == code

    def test_case_and_whitespace_are_normalised(self):
        s = state(valued("A", 60.0, 600.0, " sek "), valued("B", 40.0, 400.0, "SEK"))

        assert s.reporting_currency == "SEK"

    def test_mixed_currencies_establish_nothing(self):
        """Not "pick the biggest" and not "pick the first" -- a mixed state has
        no single denomination, and saying so is the only honest answer."""
        s = state(valued("A", 60.0, 600.0, "SEK"), valued("B", 40.0, 400.0, "USD"))

        assert s.reporting_currency is None

    def test_no_currency_reported_establishes_nothing(self):
        assert state(valued("A", 100.0, 1000.0, None)).reporting_currency is None

    def test_a_blank_currency_is_absence_not_a_value(self):
        assert state(valued("A", 100.0, 1000.0, "   ")).reporting_currency is None

    def test_a_weight_only_portfolio_establishes_nothing(self):
        """There is no amount to denominate, so there is nothing to say."""
        s = state(AlphaHolding(ticker="A", weight_percent=100.0, currency="SEK"))

        assert s.reporting_currency is None

    def test_an_empty_portfolio_establishes_nothing(self):
        assert state().reporting_currency is None

    def test_only_valued_holdings_are_consulted(self):
        """A weight-only line alongside valued ones must not make the
        portfolio look mixed -- it carries no amount to denominate."""
        s = state(
            valued("A", 60.0, 600.0, "SEK"),
            AlphaHolding(ticker="B", weight_percent=40.0, currency="EUR"),
        )

        assert s.reporting_currency == "SEK"


class TestTheViewCarriesItToTheClient:
    def _view(self, s: AlphaPortfolioState) -> PortfolioView:
        return PortfolioView.from_domain(s, derive_portfolio_view(s))

    @pytest.mark.parametrize("code", ["SEK", "USD", "EUR"])
    def test_the_currency_reaches_the_wire(self, code):
        view = self._view(state(valued("A", 60.0, 600.0, code), valued("B", 40.0, 400.0, code)))

        assert view.currency == code
        assert "currency" in view.model_dump()

    def test_an_unestablished_currency_reaches_the_wire_as_null(self):
        view = self._view(state(valued("A", 60.0, 600.0, "SEK"), valued("B", 40.0, 400.0, "USD")))

        assert view.currency is None

    def test_the_numbers_themselves_are_untouched(self):
        """Requirement 8: nothing here converts or rounds. 2,543,747 SEK stays
        2,543,747 -- only its label was ever wrong."""
        view = self._view(state(valued("A", 60.0, 1_543_747.0, "SEK"),
                                valued("B", 40.0, 1_000_000.0, "SEK")))

        assert view.total_value == pytest.approx(2_543_747.0)
        assert [h.value_absolute for h in view.holdings] == [1_543_747.0, 1_000_000.0]
        assert [h.currency for h in view.holdings] == ["SEK", "SEK"]

    def test_cash_shares_the_portfolio_denomination(self):
        view = self._view(state(valued("A", 90.0, 900.0, "SEK"), cash_value=100.0,
                                cash_weight=10.0))

        assert view.currency == "SEK"
        assert view.cash_value_absolute == pytest.approx(100.0)

    def test_an_empty_view_has_no_currency(self):
        assert PortfolioView.empty().currency is None
