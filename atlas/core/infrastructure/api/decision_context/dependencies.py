"""Composition wiring for the Decision Context API.

Reuses API-001's shared engine and DecisionRepository provider directly —
one physical database, one place that constructs the Decision-side
dependency — rather than duplicating that wiring here.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.decision_context.capture_decision_context import (
    CaptureDecisionContextService,
)
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.persistence.decision_context.sqlalchemy_repository import (
    SqlAlchemyDecisionContextRepository,
)
from atlas.core.infrastructure.persistence.decision_context.table import (
    create_decision_context_table,
)


def get_decision_context_repository(
    engine: Engine = Depends(get_decision_engine),
) -> DecisionContextRepository:
    create_decision_context_table(engine)
    return SqlAlchemyDecisionContextRepository(engine)


def get_capture_decision_context_service(
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    decision_context_repository: DecisionContextRepository = Depends(
        get_decision_context_repository
    ),
) -> CaptureDecisionContextService:
    return CaptureDecisionContextService(decision_repository, decision_context_repository)
