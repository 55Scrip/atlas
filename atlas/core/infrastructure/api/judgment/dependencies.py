"""Composition wiring for the Judgment API.

**Widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md, and widened
again to include Reasoning Trace per the Reasoning Trace Implementation
Design's own Section 34 follow-on classification**: `JudgmentService`
depends on its own repository plus `KnowledgeReferenceRepository`,
`ObservationRepository`, `DecisionRepository`, `OutcomeRepository`, and
`ReasoningTraceRepository` — Judgment's subject reference may now
target any of the six adopted types (see `capture_judgment.py`'s own
module docstring). `get_outcome_repository` and
`_get_reasoning_trace_repository` are both imported from
`knowledge_reference/dependencies.py` (their definitive home — Outcome
because no `atlas/core/infrastructure/api/outcome/` module exists;
Reasoning Trace's private provider because that module already resolves
the same import-cycle constraint for the identical reason), exactly as
`get_knowledge_reference_repository` already was.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file), exactly like every other module in this
codebase.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.judgment.capture_judgment import JudgmentService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.judgment.repository import JudgmentRepository
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.reasoning_trace.repository import ReasoningTraceRepository
from atlas.core.infrastructure.api.decision.dependencies import (
    get_decision_engine,
    get_decision_repository,
)
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    _get_reasoning_trace_repository,
    get_knowledge_reference_repository,
    get_outcome_repository,
)
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.judgment.sqlalchemy_repository import (
    SqlAlchemyJudgmentRepository,
)
from atlas.core.infrastructure.persistence.judgment.table import create_judgment_table


def get_judgment_repository(
    engine: Engine = Depends(get_decision_engine),
) -> JudgmentRepository:
    create_judgment_table(engine)
    return SqlAlchemyJudgmentRepository(engine)


def get_judgment_service(
    repository: JudgmentRepository = Depends(get_judgment_repository),
    knowledge_reference_repository: KnowledgeReferenceRepository = Depends(
        get_knowledge_reference_repository
    ),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    reasoning_trace_repository: ReasoningTraceRepository = Depends(_get_reasoning_trace_repository),
) -> JudgmentService:
    return JudgmentService(
        repository,
        knowledge_reference_repository,
        observation_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
    )
