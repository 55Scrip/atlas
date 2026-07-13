"""Composition wiring for the Observation Capture API.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file) — a read-only import, not a modification to
API-001.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.observation.capture_observation import CaptureObservationService
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table


def get_observation_repository(
    engine: Engine = Depends(get_decision_engine),
) -> ObservationRepository:
    create_observation_table(engine)
    return SqlAlchemyObservationRepository(engine)


def get_capture_observation_service(
    repository: ObservationRepository = Depends(get_observation_repository),
) -> CaptureObservationService:
    return CaptureObservationService(repository)
