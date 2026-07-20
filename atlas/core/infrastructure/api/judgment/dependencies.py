"""Composition wiring for the Judgment API.

`JudgmentService` depends on its own repository plus
`KnowledgeReferenceRepository`, reused directly from the already-wired
Knowledge Reference module — Judgment's subject reference may currently
target a Knowledge Reference or another Judgment (see
`capture_judgment.py`'s own module docstring); no Observation, Decision,
Outcome, or Reasoning Trace collaborator is wired here, since none of
those types is currently capture-enabled as a subject.

Reuses the shared engine from `decision`'s dependencies module (same
physical `atlas.db` file), exactly like every other module in this
codebase.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.core.application.judgment.capture_judgment import JudgmentService
from atlas.core.domain.judgment.repository import JudgmentRepository
from atlas.core.domain.knowledge_reference.repository import KnowledgeReferenceRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    get_knowledge_reference_repository,
)
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
) -> JudgmentService:
    return JudgmentService(repository, knowledge_reference_repository)
