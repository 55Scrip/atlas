"""Composition wiring for the unified import preview endpoint.

Reuses `atlas.alpha.portfolio.api.dependencies.get_alpha_portfolio_store`
read-only, exactly like `portfolio_fit`/other Alpha packages already
compose across module boundaries -- only to read the current holdings'
tickers for against-existing-portfolio duplicate detection; nothing
here ever writes to that store.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService


def get_portfolio_import_preview_service() -> PortfolioImportPreviewService:
    return PortfolioImportPreviewService()


def get_existing_tickers(
    store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
) -> frozenset[str]:
    state = store.get()
    if state is None:
        return frozenset()
    return frozenset(holding.ticker for holding in state.holdings)
