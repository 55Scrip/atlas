"""SQLAlchemy-backed ReasoningTraceRepository.

`add` performs one atomic transaction: a single INSERT into the parent
table (`reasoning_traces`) followed by one multi-row INSERT into the
child table (`reasoning_trace_supports`) — both within the same
`engine.begin()` block, so a Reasoning Trace is never persisted with a
partial support set (docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 30).

`get` reconstructs via the entity's ordinary constructor, not a
separate, unchecked path — so `ReasoningTrace.__post_init__`'s
non-empty check runs on reconstruction exactly as it does on capture.
A parent row with zero matching support rows can only arise from direct
database manipulation outside this repository's own `add()`; if it ever
occurs, reconstruction raises `EmptySupportError` from the entity's own
`__post_init__` rather than silently returning an entity with an empty
`frozenset` — a loud failure on tampered or corrupted data, consistent
with this codebase's general stance of trusting its own transactional
invariants.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    reasoning_trace_supports_table,
    reasoning_traces_table,
)


class SqlAlchemyReasoningTraceRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, reasoning_trace: ReasoningTrace) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(reasoning_traces_table).values(**_to_parent_row(reasoning_trace))
            )
            connection.execute(
                insert(reasoning_trace_supports_table),
                _to_support_rows(reasoning_trace),
            )

    def get(self, reasoning_trace_id: ReasoningTraceId) -> ReasoningTrace | None:
        with self._engine.connect() as connection:
            parent_row = (
                connection.execute(
                    select(reasoning_traces_table).where(
                        reasoning_traces_table.c.reasoning_trace_id == str(reasoning_trace_id)
                    )
                )
                .mappings()
                .first()
            )
            if parent_row is None:
                return None
            support_rows = (
                connection.execute(
                    select(reasoning_trace_supports_table).where(
                        reasoning_trace_supports_table.c.reasoning_trace_id
                        == str(reasoning_trace_id)
                    )
                )
                .mappings()
                .all()
            )
        return _to_reasoning_trace(parent_row, support_rows)


def _to_parent_row(reasoning_trace: ReasoningTrace) -> dict[str, Any]:
    return {
        "reasoning_trace_id": str(reasoning_trace.id),
        "case_id": str(reasoning_trace.case_id),
        "recorded_at": reasoning_trace.recorded_at.isoformat(),
    }


def _to_support_rows(reasoning_trace: ReasoningTrace) -> list[dict[str, Any]]:
    return [
        {
            "reasoning_trace_support_id": str(uuid.uuid4()),
            "reasoning_trace_id": str(reasoning_trace.id),
            "target_type": support.target_type.value,
            "target_id": str(support.target_id),
        }
        for support in reasoning_trace.supports
    ]


def _to_reasoning_trace(
    parent_row: Mapping[str, Any], support_rows: Sequence[Mapping[str, Any]]
) -> ReasoningTrace:
    return ReasoningTrace(
        id=ReasoningTraceId(uuid.UUID(parent_row["reasoning_trace_id"])),
        case_id=CaseId(uuid.UUID(parent_row["case_id"])),
        supports=frozenset(
            TypedDomainObjectReference(
                target_type=DomainObjectType(row["target_type"]),
                target_id=uuid.UUID(row["target_id"]),
            )
            for row in support_rows
        ),
        recorded_at=datetime.fromisoformat(parent_row["recorded_at"]),
    )
