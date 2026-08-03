"""Composition wiring for the Evidence Capture API.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file) — a read-only import, not a modification to
API-001.

Atlas Alpha, Evidence Sprint 1: also reuses Observation's own repository
provider directly (`get_observation_repository`), the same pattern
`decision_context`'s dependencies module already uses to reuse
`get_decision_repository` — one physical database, one place that
constructs each aggregate's own repository, rather than duplicating that
wiring here.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.evidence.capture_evidence import EvidenceService
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.evidence.sqlalchemy_repository import (
    SqlAlchemyEvidenceRepository,
)
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table


def get_evidence_repository(
    engine: Engine = Depends(get_decision_engine),
) -> EvidenceRepository:
    create_evidence_table(engine)
    return SqlAlchemyEvidenceRepository(engine)


def get_evidence_service(
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    evidence_repository: EvidenceRepository = Depends(get_evidence_repository),
) -> EvidenceService:
    return EvidenceService(observation_repository, evidence_repository)
