"""Composition wiring for the Evidence Timeline API and snapshot store.
Same "each Alpha package wires its own dependencies" convention every
sibling package's own `api/dependencies.py` documents.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.evidence_timeline.service import EvidenceTimelineService
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["get_evidence_snapshot_repository", "get_evidence_timeline_service"]


def get_evidence_snapshot_repository(engine: Engine = Depends(get_decision_engine)) -> SqlAlchemyEvidenceSnapshotRepository:
    create_evidence_snapshot_table(engine)
    return SqlAlchemyEvidenceSnapshotRepository(engine)


def get_evidence_timeline_service(
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    snapshot_repository: SqlAlchemyEvidenceSnapshotRepository = Depends(get_evidence_snapshot_repository),
) -> EvidenceTimelineService:
    return EvidenceTimelineService(
        portfolio_store=portfolio_store, watchlist_store=watchlist_store, snapshot_repository=snapshot_repository
    )
