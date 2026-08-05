"""Composition wiring for the Alpha Portfolio API.

Reuses the shared Core engine (`get_decision_engine`, same physical
`atlas.db` file) exactly like Case's own dependencies module does — a
read-only import from `atlas.core`, not a modification to it. This is an
infrastructure convenience (one SQLite file, separate tables), not a
Core-to-Alpha dependency: `atlas/core/` itself never imports anything
from `atlas/alpha/` (enforced by `tests/test_architecture_boundaries.py`).

Sprint 1B: `get_outcome_repository` is reused directly from Outcome's own
composition module (`knowledge_reference/dependencies.py`, its
established home) -- the same read-only repository Outcome's own API
already uses to read itself, never a new write path. This is the
concrete implementation of "The Alpha layer may reference Outcome" for
`apply_confirmed_trade`.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio.service import AlphaPortfolioService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository


def get_alpha_portfolio_store(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaPortfolioStore:
    create_alpha_portfolio_state_table(engine)
    return AlphaPortfolioStore(engine)


def get_alpha_trade_log_store(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaTradeLogStore:
    create_alpha_trade_log_table(engine)
    return AlphaTradeLogStore(engine)


def get_alpha_portfolio_service(
    store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    trade_log_store: AlphaTradeLogStore = Depends(get_alpha_trade_log_store),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
) -> AlphaPortfolioService:
    return AlphaPortfolioService(store, trade_log_store, outcome_repository)
