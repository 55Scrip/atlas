"""SQLAlchemy-backed InterpretationRepository."""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.interpretation.entity import Interpretation
from atlas.core.domain.interpretation.value_objects import InterpretationId, Statement
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.interpretation.table import interpretations_table


class SqlAlchemyInterpretationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, interpretation: Interpretation) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(interpretations_table).values(**_to_row(interpretation)))

    def get(self, interpretation_id: InterpretationId) -> Interpretation | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(interpretations_table).where(
                    interpretations_table.c.interpretation_id == str(interpretation_id)
                )
            ).mappings().first()
        return _to_interpretation(row) if row is not None else None

    def list_all(self) -> list[Interpretation]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(interpretations_table).order_by(interpretations_table.c.recorded_at)
            ).mappings().all()
        interpretations = [_to_interpretation(row) for row in rows]
        interpretations.sort(key=lambda i: (i.interpreted_at, i.recorded_at, i.id.value))
        return interpretations

    def list_by_observation_id(self, observation_id: ObservationId) -> list[Interpretation]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(interpretations_table)
                .where(interpretations_table.c.observation_id == str(observation_id))
                .order_by(interpretations_table.c.recorded_at)
            ).mappings().all()
        interpretations = [_to_interpretation(row) for row in rows]
        interpretations.sort(key=lambda i: (i.interpreted_at, i.recorded_at, i.id.value))
        return interpretations


def _to_row(interpretation: Interpretation) -> dict[str, Any]:
    return {
        "interpretation_id": str(interpretation.id),
        "observation_id": str(interpretation.observation_id),
        "statement": interpretation.statement.value,
        "note": interpretation.note,
        "interpreted_at": interpretation.interpreted_at.isoformat(),
        "recorded_at": interpretation.recorded_at.isoformat(),
    }


def _to_interpretation(row: Mapping[str, Any]) -> Interpretation:
    return Interpretation(
        id=InterpretationId(uuid.UUID(row["interpretation_id"])),
        observation_id=ObservationId(uuid.UUID(row["observation_id"])),
        statement=Statement(row["statement"]),
        interpreted_at=datetime.fromisoformat(row["interpreted_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
