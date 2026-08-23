"""FastAPI DI wiring for Evidence Graph -- reuses every existing
provider unchanged, the same "compose, never duplicate" pattern
`atlas.alpha.monitoring.api.dependencies` already established."""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_service
from atlas.core.infrastructure.api.case_condition.dependencies import get_case_condition_service
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository

__all__ = ["get_evidence_graph_service"]


def get_evidence_graph_service(
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    evidence_repository: EvidenceRepository = Depends(get_evidence_repository),
    case_condition_service: CaseConditionService = Depends(get_case_condition_service),
    assumption_service: AssumptionService = Depends(get_assumption_service),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> EvidenceGraphService:
    return EvidenceGraphService(
        composition_service,
        evidence_repository,
        case_condition_service,
        assumption_service,
        portfolio_store,
        watchlist_store,
    )
