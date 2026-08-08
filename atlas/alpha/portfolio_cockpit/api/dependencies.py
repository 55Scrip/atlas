"""Composition wiring for the Portfolio Cockpit API (ATLAS-028).

Same shared-engine pattern every prior Alpha API dependencies module
uses: one physical `atlas.db` file, read-only providers reused directly
from Case's, Decision's, Observation's, Evidence's, and Outcome's own
established composition modules, plus `PortfolioStatusService` itself
(ATLAS-015) -- no new repository implementation, no new table.

This is the first place `InvestmentCaseCompositionService` (ATLAS-027)
is wired into a FastAPI dependency graph -- `case_intelligence` composes
its own report by other means and never needed this service directly.
"""
from __future__ import annotations

from fastapi import Depends

from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_cockpit.service import PortfolioCockpitService
from atlas.alpha.portfolio_status.api.dependencies import get_portfolio_status_service
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository


def get_investment_case_composition_service(
    case_repository: CaseRepository = Depends(get_case_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    evidence_repository: EvidenceRepository = Depends(get_evidence_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    trade_log_store: AlphaTradeLogStore = Depends(get_alpha_trade_log_store),
) -> InvestmentCaseCompositionService:
    return InvestmentCaseCompositionService(
        case_repository=case_repository,
        decision_repository=decision_repository,
        observation_repository=observation_repository,
        evidence_repository=evidence_repository,
        outcome_repository=outcome_repository,
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
    )


def get_portfolio_cockpit_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    investment_case_composition_service: InvestmentCaseCompositionService = Depends(
        get_investment_case_composition_service
    ),
    portfolio_status_service: PortfolioStatusService = Depends(get_portfolio_status_service),
) -> PortfolioCockpitService:
    return PortfolioCockpitService(
        portfolio_store=portfolio_store,
        investment_case_composition_service=investment_case_composition_service,
        portfolio_status_service=portfolio_status_service,
    )
