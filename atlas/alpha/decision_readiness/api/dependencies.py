"""FastAPI DI wiring for Decision Readiness -- reuses every existing
provider unchanged, the same "compose, never duplicate" pattern
`atlas.alpha.evidence_graph.api.dependencies` already established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_readiness.repository import SqlAlchemyDecisionReadinessResultRepository
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_readiness.table import create_decision_readiness_result_table
from atlas.alpha.evidence_graph.api.dependencies import get_evidence_graph_service
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.monitoring.api.dependencies import get_monitoring_service
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_decision_readiness_result_repository", "get_decision_readiness_service"]


def get_decision_readiness_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyDecisionReadinessResultRepository:
    create_decision_readiness_result_table(engine)
    return SqlAlchemyDecisionReadinessResultRepository(engine)


def get_decision_readiness_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    stance_service: StanceService = Depends(get_stance_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    evidence_graph_service: EvidenceGraphService = Depends(get_evidence_graph_service),
    result_repository: SqlAlchemyDecisionReadinessResultRepository = Depends(get_decision_readiness_result_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> DecisionReadinessService:
    return DecisionReadinessService(
        composition_service,
        stance_service,
        monitoring_service,
        evidence_graph_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
