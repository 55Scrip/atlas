"""SQLAlchemy-backed LearningRepository."""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.learning.value_objects import LearningId, Statement
from atlas.core.infrastructure.persistence.learning.table import learnings_table


class SqlAlchemyLearningRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, learning: Learning) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(learnings_table).values(**_to_row(learning)))

    def get(self, learning_id: LearningId) -> Learning | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(learnings_table).where(learnings_table.c.learning_id == str(learning_id))
            ).mappings().first()
        return _to_learning(row) if row is not None else None

    def list_all(self) -> list[Learning]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(learnings_table).order_by(learnings_table.c.recorded_at)
            ).mappings().all()
        learnings = [_to_learning(row) for row in rows]
        learnings.sort(
            key=lambda learning: (learning.learned_at, learning.recorded_at, learning.id.value)
        )
        return learnings

    def list_by_evaluation_id(self, evaluation_id: EvaluationId) -> list[Learning]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(learnings_table)
                .where(learnings_table.c.evaluation_id == str(evaluation_id))
                .order_by(learnings_table.c.recorded_at)
            ).mappings().all()
        learnings = [_to_learning(row) for row in rows]
        learnings.sort(
            key=lambda learning: (learning.learned_at, learning.recorded_at, learning.id.value)
        )
        return learnings


def _to_row(learning: Learning) -> dict[str, Any]:
    return {
        "learning_id": str(learning.id),
        "evaluation_id": str(learning.evaluation_id),
        "statement": learning.statement.value,
        "note": learning.note,
        "learned_at": learning.learned_at.isoformat(),
        "recorded_at": learning.recorded_at.isoformat(),
    }


def _to_learning(row: Mapping[str, Any]) -> Learning:
    return Learning(
        id=LearningId(uuid.UUID(row["learning_id"])),
        evaluation_id=EvaluationId(uuid.UUID(row["evaluation_id"])),
        statement=Statement(row["statement"]),
        learned_at=datetime.fromisoformat(row["learned_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
