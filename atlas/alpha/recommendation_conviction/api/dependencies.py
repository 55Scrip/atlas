"""FastAPI DI wiring for Recommendation Conviction & Strength -- reuses
every existing provider unchanged, the same "compose, never duplicate"
pattern `atlas.alpha.investment_decision.api.dependencies` already
established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.api.dependencies import get_evidence_graph_service
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.repository import SqlAlchemyRecommendationConvictionResultRepository
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.recommendation_conviction.table import create_recommendation_conviction_result_table
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_recommendation_conviction_result_repository", "get_recommendation_conviction_service"]


def get_recommendation_conviction_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyRecommendationConvictionResultRepository:
    create_recommendation_conviction_result_table(engine)
    return SqlAlchemyRecommendationConvictionResultRepository(engine)


def get_recommendation_conviction_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    decision_readiness_service: DecisionReadinessService = Depends(get_decision_readiness_service),
    investment_decision_service: InvestmentDecisionService = Depends(get_investment_decision_service),
    evidence_graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
    result_repository: SqlAlchemyRecommendationConvictionResultRepository = Depends(
        get_recommendation_conviction_result_repository
    ),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> RecommendationConvictionService:
    return RecommendationConvictionService(
        composition_service,
        decision_readiness_service,
        investment_decision_service,
        evidence_graph_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
