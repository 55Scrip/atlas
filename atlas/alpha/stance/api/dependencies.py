"""Composition wiring for the Stance API. Same "each Alpha package
wires its own dependencies" convention `atlas.alpha.portfolio_fit.api
.dependencies`'s own module docstring documents.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore

__all__ = ["get_stance_service"]


def get_stance_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    portfolio_fit_service: PortfolioFitService = Depends(get_portfolio_fit_service),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> StanceService:
    return StanceService(
        composition_service=composition_service,
        portfolio_fit_service=portfolio_fit_service,
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
    )
