"""FastAPI DI wiring for Decision Reliability -- reuses every existing
provider unchanged, the same "compose, never duplicate" pattern
`atlas.alpha.decision_explanation.api.dependencies` already
established."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.decision_reliability.repository import SqlAlchemyDecisionReliabilityResultRepository
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.decision_reliability.table import create_decision_reliability_result_table
from atlas.alpha.evidence_quality.api.dependencies import get_evidence_quality_service
from atlas.alpha.evidence_quality.service import EvidenceQualityService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_decision_reliability_result_repository", "get_decision_reliability_service"]


def get_decision_reliability_result_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemyDecisionReliabilityResultRepository:
    create_decision_reliability_result_table(engine)
    return SqlAlchemyDecisionReliabilityResultRepository(engine)


def get_decision_reliability_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    evidence_quality_service: EvidenceQualityService = Depends(get_evidence_quality_service),
    decision_readiness_service: DecisionReadinessService = Depends(get_decision_readiness_service),
    result_repository: SqlAlchemyDecisionReliabilityResultRepository = Depends(get_decision_reliability_result_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> DecisionReliabilityService:
    return DecisionReliabilityService(
        composition_service,
        evidence_quality_service,
        decision_readiness_service,
        result_repository,
        portfolio_store,
        watchlist_store,
    )
