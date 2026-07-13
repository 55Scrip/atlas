"""SQLAlchemy-backed HypothesisRepository.

`add` is the only write operation and is always an INSERT. No foreign
keys, no uniqueness constraint beyond the primary key — Hypothesis has no
cross-aggregate invariant to enforce.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.hypothesis.value_objects import HypothesisId, Statement
from atlas.core.infrastructure.persistence.hypothesis.table import hypotheses_table


class SqlAlchemyHypothesisRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, hypothesis: Hypothesis) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(hypotheses_table).values(**_to_row(hypothesis)))

    def get(self, hypothesis_id: HypothesisId) -> Hypothesis | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(hypotheses_table).where(
                    hypotheses_table.c.hypothesis_id == str(hypothesis_id)
                )
            ).mappings().first()
        return _to_hypothesis(row) if row is not None else None

    def list_all(self) -> list[Hypothesis]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(hypotheses_table).order_by(hypotheses_table.c.recorded_at)
            ).mappings().all()
        hypotheses = [_to_hypothesis(row) for row in rows]
        # formulated_at preserves its investor-supplied offset (not
        # normalized to UTC), so a text-based ORDER BY on that column would
        # not reflect true chronological order across mixed offsets. Sort
        # here instead, comparing tz-aware datetimes (which compare by
        # absolute instant regardless of stored offset) — formulated_at
        # ascending, then recorded_at, then hypothesis_id as the
        # deterministic final tie-breaker.
        hypotheses.sort(key=lambda h: (h.formulated_at, h.recorded_at, h.id.value))
        return hypotheses


def _to_row(hypothesis: Hypothesis) -> dict[str, Any]:
    return {
        "hypothesis_id": str(hypothesis.id),
        "statement": hypothesis.statement.value,
        "note": hypothesis.note,
        "formulated_at": hypothesis.formulated_at.isoformat(),
        "recorded_at": hypothesis.recorded_at.isoformat(),
    }


def _to_hypothesis(row: Mapping[str, Any]) -> Hypothesis:
    return Hypothesis(
        id=HypothesisId(uuid.UUID(row["hypothesis_id"])),
        statement=Statement(row["statement"]),
        formulated_at=datetime.fromisoformat(row["formulated_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
