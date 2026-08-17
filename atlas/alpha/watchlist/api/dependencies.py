"""Composition wiring for the Alpha Watchlist API.

Reuses the shared Core engine (`get_decision_engine`) and the same
`CaseGenerationService`/`business_record_repository`/default-providers
wiring Portfolio's own dependencies module already establishes -- one
canonical Case-generation owner, one canonical default-provider set,
never a second definition of either.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.api.dependencies import (
    get_business_record_repository,
    get_default_business_data_providers,
)
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.api.dependencies import get_case_generation_service
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.service import AlphaWatchlistService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_alpha_watchlist_store(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaWatchlistStore:
    create_alpha_watchlist_entry_table(engine)
    return AlphaWatchlistStore(engine)


def get_alpha_portfolio_store_for_watchlist(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaPortfolioStore:
    """A second dependency function returning the exact same
    `AlphaPortfolioStore` shape `portfolio`'s own module already builds
    (same table, same engine) -- Watchlist reads Portfolio's holdings
    for cross-context Case reuse (`case_membership
    .resolve_case_id_for_ticker`), never writes to them. Named distinctly
    from `portfolio.api.dependencies.get_alpha_portfolio_store` only to
    keep each package's own dependency graph readable in FastAPI's
    dependency-injection tree, not because the underlying store differs."""
    create_alpha_portfolio_state_table(engine)
    return AlphaPortfolioStore(engine)


def get_alpha_watchlist_service(
    store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    case_generation_service: CaseGenerationService = Depends(get_case_generation_service),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store_for_watchlist),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    business_data_providers: tuple[BusinessDataProvider, ...] = Depends(get_default_business_data_providers),
) -> AlphaWatchlistService:
    return AlphaWatchlistService(
        store,
        case_generation_service,
        portfolio_store=portfolio_store,
        business_record_repository=business_record_repository,
        business_data_providers=business_data_providers,
    )
