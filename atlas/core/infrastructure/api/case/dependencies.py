"""Composition wiring for the Case API.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file), exactly like `hypothesis`, `evidence`, and
`observation` already do — a read-only import, not a modification to
API-001.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import (
    SqlAlchemyCaseRepository,
)
from atlas.core.infrastructure.persistence.case.table import create_case_table


def get_case_repository(engine: Engine = Depends(get_decision_engine)) -> CaseRepository:
    create_case_table(engine)
    return SqlAlchemyCaseRepository(engine)


def get_case_service(
    repository: CaseRepository = Depends(get_case_repository),
) -> CaseService:
    return CaseService(repository)
