"""FastAPI DI wiring for the Investment Case Lifecycle -- reuses every
existing provider unchanged, the same "compose, never duplicate"
pattern `atlas.alpha.decision_readiness.api.dependencies` already
established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case_lifecycle.repository import SqlAlchemyLifecycleSnapshotRepository
from atlas.alpha.investment_case_lifecycle.service import InvestmentCaseLifecycleService
from atlas.alpha.investment_case_lifecycle.table import create_investment_case_lifecycle_history_table
from atlas.alpha.monitoring.api.dependencies import get_monitoring_service
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_lifecycle_snapshot_repository", "get_investment_case_lifecycle_service"]


def get_lifecycle_snapshot_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyLifecycleSnapshotRepository:
    create_investment_case_lifecycle_history_table(engine)
    return SqlAlchemyLifecycleSnapshotRepository(engine)


def get_investment_case_lifecycle_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    snapshot_repository: SqlAlchemyLifecycleSnapshotRepository = Depends(get_lifecycle_snapshot_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> InvestmentCaseLifecycleService:
    return InvestmentCaseLifecycleService(
        composition_service,
        monitoring_service,
        snapshot_repository,
        portfolio_store,
        watchlist_store,
    )
