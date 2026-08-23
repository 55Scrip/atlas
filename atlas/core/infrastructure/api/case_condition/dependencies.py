"""Composition wiring for the CaseCondition API.

Reuses the shared engine and the sibling aggregates' own repository
providers directly — one physical `atlas.db` file, mirroring
`decision_draft/dependencies.py` exactly (Sprint 9).
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.domain.case.repository import CaseRepository
from atlas.core.domain.case_condition.repository import CaseConditionEventRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.persistence.case_condition.sqlalchemy_repository import (
    SqlAlchemyCaseConditionEventRepository,
)
from atlas.core.infrastructure.persistence.case_condition.table import (
    create_case_condition_events_table,
)


def get_case_condition_repository(
    engine: Engine = Depends(get_decision_engine),
) -> CaseConditionEventRepository:
    create_case_condition_events_table(engine)
    return SqlAlchemyCaseConditionEventRepository(engine)


def get_case_condition_service(
    condition_repository: CaseConditionEventRepository = Depends(get_case_condition_repository),
    case_repository: CaseRepository = Depends(get_case_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
) -> CaseConditionService:
    return CaseConditionService(condition_repository, case_repository, decision_repository)
