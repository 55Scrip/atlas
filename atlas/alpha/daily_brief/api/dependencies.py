"""Composition wiring for Daily Brief v1.

Reuses `atlas.alpha.investment_case.api.dependencies
.get_investment_case_composition_service` directly -- the one provider
that already wires both `watchlist_store` (Watchlist ticker fallback)
and `snapshot_repository` (Change Intelligence), never
`atlas.alpha.portfolio_cockpit.api.dependencies`'s own, otherwise
identically-named provider, which wires neither and would silently make
every Daily Brief entry unavailable.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.daily_brief.service import DailyBriefService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore


def get_daily_brief_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    investment_case_composition_service: InvestmentCaseCompositionService = Depends(
        get_investment_case_composition_service
    ),
) -> DailyBriefService:
    return DailyBriefService(
        portfolio_store=portfolio_store,
        watchlist_store=watchlist_store,
        investment_case_composition_service=investment_case_composition_service,
    )
