"""FastAPI DI wiring for Decision Alternatives & Opportunity Cost --
reuses every existing provider unchanged, the same "compose, never
duplicate" pattern `atlas.alpha.decision_path.api.dependencies`
already established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_path.api.dependencies import get_decision_path_service
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.opportunity_cost.repository import SqlAlchemyOpportunityCostResultRepository
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.opportunity_cost.table import create_opportunity_cost_result_table
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.api.dependencies import get_recommendation_conviction_service
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_opportunity_cost_result_repository", "get_opportunity_cost_service"]


def get_opportunity_cost_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyOpportunityCostResultRepository:
    create_opportunity_cost_result_table(engine)
    return SqlAlchemyOpportunityCostResultRepository(engine)


def get_opportunity_cost_service(
    investment_decision_service: InvestmentDecisionService = Depends(get_investment_decision_service),
    recommendation_conviction_service: RecommendationConvictionService = Depends(get_recommendation_conviction_service),
    decision_path_service: DecisionPathService = Depends(get_decision_path_service),
    result_repository: SqlAlchemyOpportunityCostResultRepository = Depends(get_opportunity_cost_result_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> OpportunityCostService:
    return OpportunityCostService(
        investment_decision_service,
        recommendation_conviction_service,
        decision_path_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
