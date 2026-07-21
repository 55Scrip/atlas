"""Composition wiring for the Reasoning Trace API.

Per docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 32: `reasoning_trace`
is a brand-new leaf module — nothing in the existing import graph
(`decision`, `observation`, `knowledge_reference`, `judgment`) imports
from it, in either direction, so all five collaborator providers are
imported here directly and publicly, with **no private helper
duplication** of the kind `knowledge_reference/dependencies.py` needed
for `_get_judgment_repository` (that duplication exists solely because
`judgment/dependencies.py` already imports from `knowledge_reference/
dependencies.py`, so the reverse import would cycle — no such cycle is
possible here).

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file), exactly like every other module in this
codebase.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.reasoning_trace.capture_reasoning_trace import ReasoningTraceService
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
from atlas.core.infrastructure.api.judgment.dependencies import get_judgment_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    get_knowledge_reference_repository,
    get_outcome_repository,
)
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.reasoning_trace.sqlalchemy_repository import (
    SqlAlchemyReasoningTraceRepository,
)
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    create_reasoning_trace_tables,
)


def get_reasoning_trace_repository(
    engine: Engine = Depends(get_decision_engine),
) -> ReasoningTraceRepository:
    create_reasoning_trace_tables(engine)
    return SqlAlchemyReasoningTraceRepository(engine)


def get_reasoning_trace_service(
    repository: ReasoningTraceRepository = Depends(get_reasoning_trace_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    knowledge_reference_repository: KnowledgeReferenceRepository = Depends(
        get_knowledge_reference_repository
    ),
    judgment_repository: JudgmentRepository = Depends(get_judgment_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
) -> ReasoningTraceService:
    return ReasoningTraceService(
        repository,
        observation_repository,
        knowledge_reference_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
    )
