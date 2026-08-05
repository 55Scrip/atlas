"""Composition wiring for the Alpha Portfolio API.

Reuses the shared Core engine (`get_decision_engine`, same physical
`atlas.db` file) exactly like Case's own dependencies module does — a
read-only import from `atlas.core`, not a modification to it. This is an
infrastructure convenience (one SQLite file, separate tables), not a
Core-to-Alpha dependency: `atlas/core/` itself never imports anything
from `atlas/alpha/` (enforced by `tests/test_architecture_boundaries.py`).
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio.service import AlphaPortfolioService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_alpha_portfolio_store(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaPortfolioStore:
    create_alpha_portfolio_state_table(engine)
    return AlphaPortfolioStore(engine)


def get_alpha_portfolio_service(
    store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
) -> AlphaPortfolioService:
    return AlphaPortfolioService(store)
