"""Composition wiring for the Decision Capture API.

FastAPI's dependency overrides are the seam tests use to swap the real
sqlite-backed engine for an isolated in-memory one — nothing else in the
router or application service needs to change for that.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from atlas.config import DATABASE_PATH
from atlas.core.application.decision.capture_decision import CaptureDecisionService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table


@lru_cache
def get_decision_engine() -> Engine:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DATABASE_PATH}", future=True)
    create_decision_table(engine)
    return engine


def get_decision_repository(
    engine: Engine = Depends(get_decision_engine),
) -> DecisionRepository:
    return SqlAlchemyDecisionRepository(engine)


def get_capture_decision_service(
    repository: DecisionRepository = Depends(get_decision_repository),
) -> CaptureDecisionService:
    return CaptureDecisionService(repository)
