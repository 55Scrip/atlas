"""FastAPI DI wiring for Portfolio Decision Synthesis -- reuses every
existing provider unchanged, the same "compose, never duplicate"
pattern `atlas.alpha.decision_reliability.api.dependencies` already
established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_reliability.api.dependencies import get_decision_reliability_service
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.opportunity_cost.api.dependencies import get_opportunity_cost_service
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_decision.repository import SqlAlchemyPortfolioDecisionResultRepository
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService
from atlas.alpha.portfolio_decision.table import create_portfolio_decision_result_table
from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.portfolio_intelligence.api.dependencies import get_portfolio_intelligence_service
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_portfolio_decision_result_repository", "get_portfolio_decision_service"]


def get_portfolio_decision_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyPortfolioDecisionResultRepository:
    create_portfolio_decision_result_table(engine)
    return SqlAlchemyPortfolioDecisionResultRepository(engine)


def get_portfolio_decision_service(
    investment_decision_service: InvestmentDecisionService = Depends(get_investment_decision_service),
    decision_reliability_service: DecisionReliabilityService = Depends(get_decision_reliability_service),
    opportunity_cost_service: OpportunityCostService = Depends(get_opportunity_cost_service),
    portfolio_fit_service: PortfolioFitService = Depends(get_portfolio_fit_service),
    portfolio_intelligence_service: PortfolioIntelligenceService = Depends(get_portfolio_intelligence_service),
    result_repository: SqlAlchemyPortfolioDecisionResultRepository = Depends(get_portfolio_decision_result_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> PortfolioDecisionService:
    return PortfolioDecisionService(
        investment_decision_service,
        decision_reliability_service,
        opportunity_cost_service,
        portfolio_fit_service,
        portfolio_intelligence_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
