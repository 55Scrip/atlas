"""SQLAlchemy-backed ObservationRepository.

`add` is the only write operation and is always an INSERT. No foreign keys,
no uniqueness constraint beyond the primary key — Observation has no
cross-aggregate invariant to enforce.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import ObservationId, Statement, Subject
from atlas.core.infrastructure.persistence.observation.table import observations_table


class SqlAlchemyObservationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, observation: Observation) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(observations_table).values(**_to_row(observation)))

    def get(self, observation_id: ObservationId) -> Observation | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(observations_table).where(
                    observations_table.c.observation_id == str(observation_id)
                )
            ).mappings().first()
        return _to_observation(row) if row is not None else None

    def list_all(self) -> list[Observation]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(observations_table).order_by(observations_table.c.recorded_at)
            ).mappings().all()
        return [_to_observation(row) for row in rows]


def _to_row(observation: Observation) -> dict[str, Any]:
    return {
        "observation_id": str(observation.id),
        "subject": observation.subject.value,
        "statement": observation.statement.value,
        "source": observation.source,
        "note": observation.note,
        "observed_at": observation.observed_at.isoformat(),
        "recorded_at": observation.recorded_at.isoformat(),
    }


def _to_observation(row: Mapping[str, Any]) -> Observation:
    return Observation(
        id=ObservationId(uuid.UUID(row["observation_id"])),
        subject=Subject(row["subject"]),
        statement=Statement(row["statement"]),
        observed_at=datetime.fromisoformat(row["observed_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        source=row["source"],
        note=row["note"],
    )
