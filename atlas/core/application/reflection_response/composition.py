"""Composition root for Reflection Response (ATLAS-009).

The only place aware of a SQLAlchemy Engine for this capability. Not
imported by pattern_recognition/strategy_signature/decision_reflection/
decision_coach's own composition roots — Reflection Response is
read-isolated from every other capability (ATLAS-009-D §12, invariant
15's own inverse: no other capability may consume it).
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.core.application.reflection_response.capture_reflection_response import (
    CaptureReflectionResponseService,
)
from atlas.core.infrastructure.persistence.reflection_response.sqlalchemy_repository import (
    SqlAlchemyReflectionResponseRepository,
)
from atlas.core.infrastructure.persistence.reflection_response.table import (
    create_reflection_response_table,
)


def create_reflection_response_tables(engine: Engine) -> None:
    create_reflection_response_table(engine)


def build_capture_reflection_response_service(engine: Engine) -> CaptureReflectionResponseService:
    return CaptureReflectionResponseService(SqlAlchemyReflectionResponseRepository(engine))
