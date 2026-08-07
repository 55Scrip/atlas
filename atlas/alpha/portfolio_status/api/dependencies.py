"""Composition wiring for the Portfolio Status API (ATLAS-015).

Same shared-engine pattern `atlas/alpha/portfolio/api/dependencies.py`
already uses: one physical `atlas.db` file via `get_decision_engine`,
read-only providers reused directly from Decision's, Observation's, and
Outcome's own established composition modules -- no new repository
implementation, no new table.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store, get_alpha_trade_log_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository


def get_portfolio_status_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    trade_log_store: AlphaTradeLogStore = Depends(get_alpha_trade_log_store),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
) -> PortfolioStatusService:
    return PortfolioStatusService(
        portfolio_store=portfolio_store,
        trade_log_store=trade_log_store,
        decision_repository=decision_repository,
        outcome_repository=outcome_repository,
        observation_repository=observation_repository,
    )


# Re-exported so tests overriding the shared engine only need one import.
__all__ = ["get_portfolio_status_service", "get_decision_engine"]
