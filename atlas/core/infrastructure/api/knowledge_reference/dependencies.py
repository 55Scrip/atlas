"""Composition wiring for the Knowledge Reference API.

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2, and
widened per docs/atlas_domain_object_architecture/
Reference-Validation-Availability-Implementation-Design.md**:
`KnowledgeReferenceService` now depends on Observation, Judgment,
Decision, and Outcome repositories in addition to its own, since all
four are now capture-enabled target types (see
`capture_knowledge_reference.py`'s own module docstring). Reasoning
Trace remains the only target type with no collaborator repository
wired here, since it has no repository at all anywhere in this
codebase.

`get_outcome_repository` is defined here, not in a dedicated
`atlas/core/infrastructure/api/outcome/` module, because no such module
exists — Outcome has no REST API of its own (Section 6 of the design
cited above). `_get_judgment_repository` is defined here, privately,
rather than imported from `judgment/dependencies.py`'s own
`get_judgment_repository`, specifically to avoid a circular import:
`judgment/dependencies.py` already imports from this module, so this
module must not import from it in return (see the design's own Section
6 for the verified import-cycle analysis this resolves).

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


def get_knowledge_reference_service(
    repository: KnowledgeReferenceRepository = Depends(get_knowledge_reference_repository),
    observation_repository: ObservationRepository = Depends(get_observation_repository),
    judgment_repository: JudgmentRepository = Depends(_get_judgment_repository),
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
) -> KnowledgeReferenceService:
    return KnowledgeReferenceService(
        repository,
        observation_repository,
        judgment_repository,
        decision_repository,
        outcome_repository,
    )
