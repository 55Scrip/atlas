"""Composition wiring for the Portfolio Intelligence API (ATLAS-016).

Same shared-engine pattern `atlas/alpha/portfolio_status/api/dependencies.py`
already uses: one physical `atlas.db` file, read-only providers reused
directly from Decision's, Observation's, Evidence's, and Outcome's own
established composition modules, plus `PortfolioStatusService` itself
(ATLAS-015) -- no new repository implementation, no new table.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.api.dependencies import get_portfolio_status_service
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository


def get_portfolio_intelligence_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    trade_log_store: AlphaTradeLogStore = Depends(get_alpha_trade_log_store),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    evidence_repository: EvidenceRepository = Depends(get_evidence_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    portfolio_status_service: PortfolioStatusService = Depends(get_portfolio_status_service),
) -> PortfolioIntelligenceService:
    return PortfolioIntelligenceService(
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        evidence_repository=evidence_repository,
        outcome_repository=outcome_repository,
        portfolio_status_service=portfolio_status_service,
    )
