"""Composition wiring for enrichment progress -- reuses the shared Core
engine exactly like every other Alpha package's own dependencies module.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.enrichment_tracking.store import EnrichmentProgressStore
from atlas.alpha.enrichment_tracking.table import create_enrichment_progress_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_enrichment_progress_store(
    engine: Engine = Depends(get_decision_engine),
) -> EnrichmentProgressStore:
    create_enrichment_progress_table(engine)
    return EnrichmentProgressStore(engine)
