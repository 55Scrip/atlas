"""SQLAlchemy-backed OutcomeRepository."""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import OutcomeId, Statement
from atlas.core.infrastructure.persistence.outcome.table import outcomes_table


class SqlAlchemyOutcomeRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, outcome: Outcome) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(outcomes_table).values(**_to_row(outcome)))

    def get(self, outcome_id: OutcomeId) -> Outcome | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(outcomes_table).where(outcomes_table.c.outcome_id == str(outcome_id))
            ).mappings().first()
        return _to_outcome(row) if row is not None else None

    def list_all(self) -> list[Outcome]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(outcomes_table).order_by(outcomes_table.c.recorded_at)
            ).mappings().all()
        outcomes = [_to_outcome(row) for row in rows]
        outcomes.sort(key=lambda o: (o.occurred_at, o.recorded_at, o.id.value))
        return outcomes

    def list_by_decision_id(self, decision_id: DecisionId) -> list[Outcome]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(outcomes_table)
                .where(outcomes_table.c.decision_id == str(decision_id))
                .order_by(outcomes_table.c.recorded_at)
            ).mappings().all()
        outcomes = [_to_outcome(row) for row in rows]
        outcomes.sort(key=lambda o: (o.occurred_at, o.recorded_at, o.id.value))
        return outcomes


def _to_row(outcome: Outcome) -> dict[str, Any]:
    return {
        "outcome_id": str(outcome.id),
        "decision_id": str(outcome.decision_id),
        "statement": outcome.statement.value,
        "note": outcome.note,
        "occurred_at": outcome.occurred_at.isoformat(),
        "recorded_at": outcome.recorded_at.isoformat(),
    }


def _to_outcome(row: Mapping[str, Any]) -> Outcome:
    return Outcome(
        id=OutcomeId(uuid.UUID(row["outcome_id"])),
        decision_id=DecisionId(uuid.UUID(row["decision_id"])),
        statement=Statement(row["statement"]),
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
