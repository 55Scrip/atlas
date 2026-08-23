"""Composition wiring for the Assumption API.

Reuses the shared engine and the sibling aggregates' own repository
providers directly — one physical `atlas.db` file, mirroring
`case_condition/dependencies.py` exactly (Sprint 10).
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.domain.assumption.repository import AssumptionEventRepository
from atlas.core.domain.case_condition.repository import CaseConditionEventRepository
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.infrastructure.api.case_condition.dependencies import (
    get_case_condition_repository,
)
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.persistence.assumption.sqlalchemy_repository import (
    SqlAlchemyAssumptionEventRepository,
)
from atlas.core.infrastructure.persistence.assumption.table import create_assumption_events_table


def get_assumption_repository(
    engine: Engine = Depends(get_decision_engine),
) -> AssumptionEventRepository:
    create_assumption_events_table(engine)
    return SqlAlchemyAssumptionEventRepository(engine)


def get_assumption_service(
    assumption_repository: AssumptionEventRepository = Depends(get_assumption_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    case_condition_repository: CaseConditionEventRepository = Depends(
        get_case_condition_repository
    ),
) -> AssumptionService:
    return AssumptionService(assumption_repository, decision_repository, case_condition_repository)
