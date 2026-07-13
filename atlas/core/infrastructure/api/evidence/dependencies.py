"""Composition wiring for the Evidence Capture API.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file) — a read-only import, not a modification to
API-001.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.evidence.capture_evidence import EvidenceService
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
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
    repository: EvidenceRepository = Depends(get_evidence_repository),
) -> EvidenceService:
    return EvidenceService(repository)
