"""Composition wiring for the Outcome API.

`outcome` is a brand-new leaf module — nothing in the existing import
graph imports from it, so its two collaborator providers are imported
directly and publicly, with no private-helper duplication needed
(unlike `judgment/dependencies.py`'s own `_get_judgment_repository`,
needed there only because of a real, verified cycle). `get_outcome_repository`
already exists, defined in `knowledge_reference/dependencies.py` (the
established home for it, since no `atlas/core/infrastructure/api/outcome/`
module existed before this sprint) — reused unchanged here rather than
duplicated. Reuses the shared engine from `decision`'s dependencies
module (same physical `atlas.db` file), exactly like every other module
in this codebase.
"""

from __future__ import annotations

from fastapi import Depends

from atlas.core.application.outcome.capture_outcome import OutcomeService
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.knowledge_reference.dependencies import get_outcome_repository


def get_outcome_service(
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    outcome_repository: OutcomeRepository = Depends(get_outcome_repository),
) -> OutcomeService:
    return OutcomeService(decision_repository, outcome_repository)
