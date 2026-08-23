"""FastAPI DI wiring for Decision Explanation -- reuses every existing
provider unchanged, the same "compose, never duplicate" pattern
`atlas.alpha.decision_memory.api.dependencies` already established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_explanation.repository import SqlAlchemyDecisionExplanationResultRepository
from atlas.alpha.decision_explanation.service import DecisionExplanationService
from atlas.alpha.decision_explanation.table import create_decision_explanation_result_table
from atlas.alpha.decision_memory.api.dependencies import get_decision_memory_service
from atlas.alpha.decision_memory.service import DecisionMemoryService
from atlas.alpha.decision_path.api.dependencies import get_decision_path_service
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.api.dependencies import get_evidence_graph_service
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.recommendation_conviction.api.dependencies import get_recommendation_conviction_service
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_decision_explanation_result_repository", "get_decision_explanation_service"]


def get_decision_explanation_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyDecisionExplanationResultRepository:
    create_decision_explanation_result_table(engine)
    return SqlAlchemyDecisionExplanationResultRepository(engine)


def get_decision_explanation_service(
    investment_decision_service: InvestmentDecisionService = Depends(get_investment_decision_service),
    recommendation_conviction_service: RecommendationConvictionService = Depends(get_recommendation_conviction_service),
    decision_readiness_service: DecisionReadinessService = Depends(get_decision_readiness_service),
    decision_path_service: DecisionPathService = Depends(get_decision_path_service),
    decision_memory_service: DecisionMemoryService = Depends(get_decision_memory_service),
    evidence_graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
    result_repository: SqlAlchemyDecisionExplanationResultRepository = Depends(get_decision_explanation_result_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> DecisionExplanationService:
    return DecisionExplanationService(
        investment_decision_service,
        recommendation_conviction_service,
        decision_readiness_service,
        decision_path_service,
        decision_memory_service,
        evidence_graph_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
