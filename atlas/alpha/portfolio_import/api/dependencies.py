"""Composition wiring for the unified import preview endpoint.

Reuses `atlas.alpha.portfolio.api.dependencies.get_alpha_portfolio_store`
read-only, exactly like `portfolio_fit`/other Alpha packages already
compose across module boundaries -- only to read the current holdings'
tickers for against-existing-portfolio duplicate detection; nothing
here ever writes to that store.

`get_security_discovery_indexes` is reused directly from
`security_discovery`'s own composition module -- same process-local
cached `SecTitleIndexSource` singleton every other caller of that
service shares, not a second fetch/cache built here.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_import.resolution_service import DiscoverFn
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService
from atlas.alpha.security_discovery.api.dependencies import get_security_discovery_indexes
from atlas.alpha.security_discovery.models import SecurityCandidate
from atlas.alpha.security_discovery.service import (
    TickerIndex,
    TitleIndex,
    discover_security_candidates,
)


def get_portfolio_import_preview_service() -> PortfolioImportPreviewService:
    return PortfolioImportPreviewService()


def get_existing_tickers(
    store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
) -> frozenset[str]:
    state = store.get()
    if state is None:
        return frozenset()
    return frozenset(holding.ticker for holding in state.holdings)


def get_security_discovery_fn(
    indexes: tuple[TitleIndex, TickerIndex] = Depends(get_security_discovery_indexes),
) -> DiscoverFn:
    title_index, ticker_index = indexes

    def _discover(query: str) -> tuple[SecurityCandidate, ...]:
        return discover_security_candidates(query, title_index=title_index, ticker_index=ticker_index)

    return _discover
