"""Composition wiring for the Hypothesis Capture API.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file) — a read-only import, not a modification to
API-001.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.hypothesis.capture_hypothesis import HypothesisService
from atlas.core.domain.hypothesis.repository import HypothesisRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.hypothesis.sqlalchemy_repository import (
    SqlAlchemyHypothesisRepository,
)
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table


def get_hypothesis_repository(
    engine: Engine = Depends(get_decision_engine),
) -> HypothesisRepository:
    create_hypothesis_table(engine)
    return SqlAlchemyHypothesisRepository(engine)


def get_hypothesis_service(
    repository: HypothesisRepository = Depends(get_hypothesis_repository),
) -> HypothesisService:
    return HypothesisService(repository)
