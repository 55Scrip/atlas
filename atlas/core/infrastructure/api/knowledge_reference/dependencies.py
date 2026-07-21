"""Composition wiring for the Knowledge Reference API.

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2;
widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md; widened
again to include Reasoning Trace per the Reasoning Trace Implementation
Design's own Section 34 follow-on classification**:
`KnowledgeReferenceService` now depends on Observation, Judgment,
Decision, Outcome, and Reasoning Trace repositories in addition to its
own, since all six adopted types are now capture-enabled target types
(see `capture_knowledge_reference.py`'s own module docstring).

`get_outcome_repository` is defined here, not in a dedicated
`atlas/core/infrastructure/api/outcome/` module, because no such module
exists — Outcome has no REST API of its own (Section 6 of the design
cited above). `_get_judgment_repository` and `_get_reasoning_trace_repository`
are defined here, privately, rather than imported from
`judgment/dependencies.py`'s own `get_judgment_repository` or
`reasoning_trace/dependencies.py`'s own `get_reasoning_trace_repository`,
specifically to avoid a circular import: both of those modules already
import from this one (`judgment/dependencies.py` imports
`get_knowledge_reference_repository`/`get_outcome_repository`;
`reasoning_trace/dependencies.py` imports those plus
`get_judgment_repository`), so this module must not import from either
of them in return (see the design's own Section 6 for the verified
import-cycle analysis this resolves, and Reasoning-Trace-Implementation-
Design.md Section 32 for the identical reasoning applied to Reasoning
Trace's own leaf-module position).

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file), exactly like `hypothesis`, `evidence`,
`observation`, and `case` already do.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.knowledge_reference.capture_knowledge_reference import (
    KnowledgeReferenceService,
)
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
from atlas.core.infrastructure.api.observation.dependencies import get_observation_repository
from atlas.core.infrastructure.persistence.judgment.sqlalchemy_repository import (
    SqlAlchemyJudgmentRepository,
)
from atlas.core.infrastructure.persistence.judgment.table import create_judgment_table
from atlas.core.infrastructure.persistence.knowledge_reference.sqlalchemy_repository import (
    SqlAlchemyKnowledgeReferenceRepository,
)
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    create_knowledge_reference_table,
)
from atlas.core.infrastructure.persistence.outcome.sqlalchemy_repository import (
    SqlAlchemyOutcomeRepository,
)
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table
from atlas.core.infrastructure.persistence.reasoning_trace.sqlalchemy_repository import (
    SqlAlchemyReasoningTraceRepository,
)
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    create_reasoning_trace_tables,
)


def get_knowledge_reference_repository(
    engine: Engine = Depends(get_decision_engine),
) -> KnowledgeReferenceRepository:
    create_knowledge_reference_table(engine)
    return SqlAlchemyKnowledgeReferenceRepository(engine)


def get_outcome_repository(engine: Engine = Depends(get_decision_engine)) -> OutcomeRepository:
    create_outcome_table(engine)
    return SqlAlchemyOutcomeRepository(engine)


def _get_judgment_repository(engine: Engine = Depends(get_decision_engine)) -> JudgmentRepository:
    create_judgment_table(engine)
    return SqlAlchemyJudgmentRepository(engine)


def _get_reasoning_trace_repository(
    engine: Engine = Depends(get_decision_engine),
) -> ReasoningTraceRepository:
    create_reasoning_trace_tables(engine)
    return SqlAlchemyReasoningTraceRepository(engine)


def get_knowledge_reference_service(
    repository: KnowledgeReferenceRepository = Depends(get_knowledge_reference_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    judgment_repository: JudgmentRepository = Depends(_get_judgment_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
    reasoning_trace_repository: ReasoningTraceRepository = Depends(_get_reasoning_trace_repository),
) -> KnowledgeReferenceService:
    return KnowledgeReferenceService(
        repository,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
        reasoning_trace_repository,
    )
