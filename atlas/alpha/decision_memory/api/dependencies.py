"""FastAPI DI wiring for Decision Memory -- reuses every existing
provider unchanged, the same "compose, never duplicate" pattern
`atlas.alpha.opportunity_cost.api.dependencies` already established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_memory.repository import SqlAlchemyDecisionMemoryRepository
from atlas.alpha.decision_memory.service import DecisionMemoryService
from atlas.alpha.decision_memory.table import create_decision_memory_snapshot_table
from atlas.alpha.decision_path.api.dependencies import get_decision_path_service
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.opportunity_cost.api.dependencies import get_opportunity_cost_service
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.api.dependencies import get_recommendation_conviction_service
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_decision_memory_repository", "get_decision_memory_service"]


def get_decision_memory_repository(engine: Engine = Depends(get_decision_engine)) -> SqlAlchemyDecisionMemoryRepository:
    create_decision_memory_snapshot_table(engine)
    return SqlAlchemyDecisionMemoryRepository(engine)


def get_decision_memory_service(
    investment_decision_service: InvestmentDecisionService = Depends(get_investment_decision_service),
    decision_readiness_service: DecisionReadinessService = Depends(get_decision_readiness_service),
    recommendation_conviction_service: RecommendationConvictionService = Depends(get_recommendation_conviction_service),
    decision_path_service: DecisionPathService = Depends(get_decision_path_service),
    opportunity_cost_service: OpportunityCostService = Depends(get_opportunity_cost_service),
    repository: SqlAlchemyDecisionMemoryRepository = Depends(get_decision_memory_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> DecisionMemoryService:
    return DecisionMemoryService(
        investment_decision_service,
        decision_readiness_service,
        recommendation_conviction_service,
        decision_path_service,
        opportunity_cost_service,
        repository,
        portfolio_store,
        watchlist_store,
    )
