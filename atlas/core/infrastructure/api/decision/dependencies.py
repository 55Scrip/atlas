"""Composition wiring for the Decision Capture API.

FastAPI's dependency overrides are the seam tests use to swap the real
sqlite-backed engine for an isolated in-memory one — nothing else in the
router or application service needs to change for that.

Atlas Alpha, Decision Sprint 1: `get_capture_decision_service` now also
depends on `ObservationRepository`, for the optional `observation_id`
existence/same-Case check (see `capture_decision.py`'s own module
docstring). `observation/dependencies.py` already imports
`get_decision_engine` from this module (to share the one physical
`atlas.db` engine), so importing `get_observation_repository` back from
there would cycle. `_get_observation_repository` below resolves this the
same way `knowledge_reference/dependencies.py` already resolves the
identical constraint for `_get_judgment_repository`: a private,
locally-defined provider that constructs the repository directly,
instead of importing the public one.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from atlas.config import DATABASE_PATH
from atlas.core.application.decision.capture_decision import CaptureDecisionService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.infrastructure.persistence.decision.sqlalchemy_repository import (
    SqlAlchemyDecisionRepository,
)
from atlas.core.infrastructure.persistence.decision.table import create_decision_table
from atlas.core.infrastructure.persistence.observation.sqlalchemy_repository import (
    SqlAlchemyObservationRepository,
)
from atlas.core.infrastructure.persistence.observation.table import create_observation_table


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


def _get_observation_repository(
    engine: Engine = Depends(get_decision_engine),
) -> ObservationRepository:
    create_observation_table(engine)
    return SqlAlchemyObservationRepository(engine)


def get_capture_decision_service(
    repository: DecisionRepository = Depends(get_decision_repository),
    observation_repository: ObservationRepository = Depends(_get_observation_repository),
) -> CaptureDecisionService:
    return CaptureDecisionService(repository, observation_repository)
