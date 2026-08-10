"""Composition wiring for History v1.

Reuses `atlas.alpha.investment_case_change.api.dependencies
.get_investment_case_snapshot_repository` directly for the snapshot
repository -- the same repository Daily Brief and Investment Case
composition already share, never a second connection to the same table.
Deliberately does NOT depend on `InvestmentCaseCompositionService`
(unlike Daily Brief's own dependencies module): History must never be
able to call `.build()`/`.build_many()`, which would persist a new
snapshot as a side effect -- see `InvestmentCaseHistoryService`'s own
read-only guarantee.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.investment_case_change.api.dependencies import get_investment_case_snapshot_repository
from atlas.alpha.investment_case_change.repository import SqlAlchemyInvestmentCaseSnapshotRepository
from atlas.alpha.investment_case_history.service import InvestmentCaseHistoryService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore


def get_investment_case_history_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    snapshot_repository: SqlAlchemyInvestmentCaseSnapshotRepository = Depends(get_investment_case_snapshot_repository),
) -> InvestmentCaseHistoryService:
    return InvestmentCaseHistoryService(
        portfolio_store=portfolio_store, watchlist_store=watchlist_store, snapshot_repository=snapshot_repository
    )
