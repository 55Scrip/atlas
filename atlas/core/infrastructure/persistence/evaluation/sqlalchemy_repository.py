"""SQLAlchemy-backed EvaluationRepository."""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.value_objects import EvaluationId, Statement
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.infrastructure.persistence.evaluation.table import evaluations_table


class SqlAlchemyEvaluationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, evaluation: Evaluation) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(evaluations_table).values(**_to_row(evaluation)))

    def get(self, evaluation_id: EvaluationId) -> Evaluation | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(evaluations_table).where(
                    evaluations_table.c.evaluation_id == str(evaluation_id)
                )
            ).mappings().first()
        return _to_evaluation(row) if row is not None else None

    def list_all(self) -> list[Evaluation]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(evaluations_table).order_by(evaluations_table.c.recorded_at)
            ).mappings().all()
        evaluations = [_to_evaluation(row) for row in rows]
        evaluations.sort(key=lambda e: (e.evaluated_at, e.recorded_at, e.id.value))
        return evaluations

    def list_by_outcome_id(self, outcome_id: OutcomeId) -> list[Evaluation]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(evaluations_table)
                .where(evaluations_table.c.outcome_id == str(outcome_id))
                .order_by(evaluations_table.c.recorded_at)
            ).mappings().all()
        evaluations = [_to_evaluation(row) for row in rows]
        evaluations.sort(key=lambda e: (e.evaluated_at, e.recorded_at, e.id.value))
        return evaluations


def _to_row(evaluation: Evaluation) -> dict[str, Any]:
    return {
        "evaluation_id": str(evaluation.id),
        "outcome_id": str(evaluation.outcome_id),
        "statement": evaluation.statement.value,
        "note": evaluation.note,
        "evaluated_at": evaluation.evaluated_at.isoformat(),
        "recorded_at": evaluation.recorded_at.isoformat(),
    }


def _to_evaluation(row: Mapping[str, Any]) -> Evaluation:
    return Evaluation(
        id=EvaluationId(uuid.UUID(row["evaluation_id"])),
        outcome_id=OutcomeId(uuid.UUID(row["outcome_id"])),
        statement=Statement(row["statement"]),
        evaluated_at=datetime.fromisoformat(row["evaluated_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
