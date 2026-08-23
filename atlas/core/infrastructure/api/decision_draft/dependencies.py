"""Composition wiring for the DecisionDraft API.

Reuses the shared engine and the sibling aggregates' own repository
providers directly — one physical `atlas.db` file, exactly like every
other module under `atlas/core/infrastructure/api/` (see
`decision_context/dependencies.py`'s own identical pattern).
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.decision_draft.decision_draft_service import DecisionDraftService
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.domain.decision_draft.repository import DecisionDraftEventRepository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.api.decision_context.dependencies import (
    get_decision_context_repository,
)
from atlas.core.infrastructure.persistence.decision_draft.sqlalchemy_repository import (
    SqlAlchemyDecisionDraftEventRepository,
)
from atlas.core.infrastructure.persistence.decision_draft.table import (
    create_decision_draft_events_table,
)


def get_decision_draft_repository(
    engine: Engine = Depends(get_decision_engine),
) -> DecisionDraftEventRepository:
    create_decision_draft_events_table(engine)
    return SqlAlchemyDecisionDraftEventRepository(engine)


def get_decision_draft_service(
    draft_repository: DecisionDraftEventRepository = Depends(get_decision_draft_repository),
    case_repository: CaseRepository = Depends(get_case_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    decision_context_repository: DecisionContextRepository = Depends(
        get_decision_context_repository
    ),
) -> DecisionDraftService:
    return DecisionDraftService(
        draft_repository, case_repository, decision_repository, decision_context_repository
    )
