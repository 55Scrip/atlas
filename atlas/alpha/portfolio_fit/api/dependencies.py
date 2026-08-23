"""Composition wiring for the Portfolio Fit API.

Same "each Alpha package wires `InvestmentCaseCompositionService` for
itself" convention `atlas.alpha.investment_case.api.dependencies`'s own
module docstring documents -- reusing the identical construction, not a
new one.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["get_portfolio_fit_service"]


def get_portfolio_fit_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
) -> PortfolioFitService:
    return PortfolioFitService(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        composition_service=composition_service,
    )
