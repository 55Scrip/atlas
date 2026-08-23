"""FastAPI DI wiring for Investment Decision Synthesis -- reuses every
existing provider unchanged, the same "compose, never duplicate"
pattern `atlas.alpha.decision_readiness.api.dependencies` already
established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_decision.repository import SqlAlchemyInvestmentDecisionResultRepository
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.investment_decision.table import create_investment_decision_result_table
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_investment_decision_result_repository", "get_investment_decision_service"]


def get_investment_decision_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyInvestmentDecisionResultRepository:
    create_investment_decision_result_table(engine)
    return SqlAlchemyInvestmentDecisionResultRepository(engine)


def get_investment_decision_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    decision_readiness_service: DecisionReadinessService = Depends(get_decision_readiness_service),
    stance_service: StanceService = Depends(get_stance_service),
    result_repository: SqlAlchemyInvestmentDecisionResultRepository = Depends(get_investment_decision_result_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> InvestmentDecisionService:
    return InvestmentDecisionService(
        composition_service,
        decision_readiness_service,
        stance_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
