"""Composition wiring for the Knowledge Reference API.

**Corrected per docs/atlas_domain_object_architecture/
Knowledge-Reference-Pre-Commit-Architecture-Review.md, Outcome 2**:
`KnowledgeReferenceService` now depends only on its own repository —
Observation, Decision, and Outcome are canonical, reference-eligible
target types (OE-002 §5.2), but capture against them is not currently
enabled (see `capture_knowledge_reference.py`'s own module docstring),
so no collaborator repository for any of them is wired here.

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
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.knowledge_reference.sqlalchemy_repository import (
    SqlAlchemyKnowledgeReferenceRepository,
)
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    create_knowledge_reference_table,
)


def get_knowledge_reference_repository(
    engine: Engine = Depends(get_decision_engine),
) -> KnowledgeReferenceRepository:
    create_knowledge_reference_table(engine)
    return SqlAlchemyKnowledgeReferenceRepository(engine)


def get_knowledge_reference_service(
    repository: KnowledgeReferenceRepository = Depends(get_knowledge_reference_repository),
) -> KnowledgeReferenceService:
    return KnowledgeReferenceService(repository)
