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

from atlas.alpha.business_data_refresh.api.dependencies import (
    get_business_record_repository,
    get_canonical_security_identity_gate,
    get_default_business_data_providers,
)
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.ingestion.api.dependencies import get_ingestion_result_repository
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.portfolio.service import AlphaPortfolioService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.alpha.portfolio.trade_log_table import create_alpha_trade_log_table
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.infrastructure.api.case.dependencies import get_case_service
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


def get_case_generation_service(
    case_service: CaseService = Depends(get_case_service),
) -> CaseGenerationService:
    return CaseGenerationService(case_service)


def get_alpha_watchlist_store_for_portfolio(
    engine: Engine = Depends(get_decision_engine),
) -> AlphaWatchlistStore:
    """The Portfolio-side mirror of `watchlist.api.dependencies
    .get_alpha_portfolio_store_for_watchlist` -- Portfolio reads
    Watchlist's entries for cross-context Case reuse, never writes to
    them, same table/engine either module resolves to."""
    create_alpha_watchlist_entry_table(engine)
    return AlphaWatchlistStore(engine)


def get_alpha_portfolio_service(
    store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    trade_log_store: AlphaTradeLogStore = Depends(get_alpha_trade_log_store),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    case_generation_service: CaseGenerationService = Depends(get_case_generation_service),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store_for_portfolio),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    business_data_providers: tuple[BusinessDataProvider, ...] = Depends(get_default_business_data_providers),
    identity_gate: CanonicalSecurityIdentityGate = Depends(get_canonical_security_identity_gate),
    ingestion_result_repository: SqlAlchemyIngestionResultRepository = Depends(get_ingestion_result_repository),
) -> AlphaPortfolioService:
    return AlphaPortfolioService(
        store,
        trade_log_store,
        outcome_repository,
        case_generation_service,
        watchlist_store=watchlist_store,
        business_record_repository=business_record_repository,
        business_data_providers=business_data_providers,
        identity_gate=identity_gate,
        ingestion_result_repository=ingestion_result_repository,
    )
