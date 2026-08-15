"""Composition wiring for Security Confirmation. Same shared-engine
pattern every other repository's dependencies module uses -- one
physical `atlas.db` file, reused via `decision`'s own
`get_decision_engine`/`get_decision_repository`, mirroring
`atlas.alpha.investment_case_change.api.dependencies` exactly.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_confirmation.service import ConfirmSecuritySelectionService
from atlas.alpha.security_confirmation.table import create_security_confirmation_table
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)


def get_security_confirmation_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemySecurityConfirmationRepository:
    create_security_confirmation_table(engine)
    return SqlAlchemySecurityConfirmationRepository(engine)


def get_confirm_security_selection_service(
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    confirmation_repository: SqlAlchemySecurityConfirmationRepository = Depends(
        get_security_confirmation_repository
    ),
) -> ConfirmSecuritySelectionService:
    return ConfirmSecuritySelectionService(decision_repository, confirmation_repository)
