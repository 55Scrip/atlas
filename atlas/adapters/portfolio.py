"""Adapter from the legacy portfolio JSON shape to the Portfolio Domain.

The legacy CLI portfolio file format (`atlas.analysis.portfolio.Portfolio`,
used by `atlas portfolio analyze` and `atlas portfolio review`) stores
positions as a relative `weight` with no absolute currency market value:

    {"ticker": "NVDA", "company": "...", "sector": "...", "country": "...",
     "market_cap": 0, "weight": 0.12, "quality_score": 80, "risk_score": 40}

The Portfolio Domain (`atlas.domains.portfolio`) expects
`atlas.shared.Holding.market_value` to carry an absolute currency amount, and
derives weights from it.

Because the legacy format never recorded an absolute position size, this
adapter uses each position's `weight` directly as a stand-in market value.
This is deterministic and preserves all *relative* domain calculations
(sector/country allocation, concentration, top holdings) exactly, since those
calculations only depend on relative proportions between holdings. It does
not preserve a meaningful absolute `total_value` in currency terms -- callers
that need real currency totals should not rely on this adapter.
"""

from __future__ import annotations

from atlas.analysis.portfolio import Portfolio as LegacyPortfolio
from atlas.shared import Holding, Portfolio

DEFAULT_PORTFOLIO_ID = "legacy-portfolio"
DEFAULT_PORTFOLIO_NAME = "Legacy Portfolio"


def legacy_portfolio_to_domain_portfolio(
    legacy_portfolio: LegacyPortfolio,
    portfolio_id: str = DEFAULT_PORTFOLIO_ID,
    portfolio_name: str = DEFAULT_PORTFOLIO_NAME,
) -> Portfolio:
    """Translate a legacy CLI portfolio into a Portfolio Domain entity.

    Deterministic, performs no I/O, and does not mutate its input.
    """

    holdings = tuple(
        Holding(
            company_id=position.ticker,
            ticker=position.ticker,
            quantity=0.0,
            current_price=None,
            market_value=position.weight,
            weight=0.0,
            sector=position.sector,
            country=position.country,
            currency="USD",
            asset_type="equity",
        )
        for position in legacy_portfolio.positions
    )
    return Portfolio(
        id=portfolio_id,
        name=portfolio_name,
        holdings=holdings,
    )
