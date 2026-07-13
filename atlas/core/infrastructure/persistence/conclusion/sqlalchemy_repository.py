"""SQLAlchemy-backed ConclusionRepository."""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.conclusion.entity import Conclusion
from atlas.core.domain.conclusion.value_objects import ConclusionId, Statement
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.infrastructure.persistence.conclusion.table import conclusions_table


class SqlAlchemyConclusionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, conclusion: Conclusion) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(conclusions_table).values(**_to_row(conclusion)))

    def get(self, conclusion_id: ConclusionId) -> Conclusion | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(conclusions_table).where(
                    conclusions_table.c.conclusion_id == str(conclusion_id)
                )
            ).mappings().first()
        return _to_conclusion(row) if row is not None else None

    def list_all(self) -> list[Conclusion]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(conclusions_table).order_by(conclusions_table.c.recorded_at)
            ).mappings().all()
        conclusions = [_to_conclusion(row) for row in rows]
        conclusions.sort(key=lambda c: (c.concluded_at, c.recorded_at, c.id.value))
        return conclusions

    def list_by_evidence_id(self, evidence_id: EvidenceId) -> list[Conclusion]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(conclusions_table)
                .where(conclusions_table.c.evidence_id == str(evidence_id))
                .order_by(conclusions_table.c.recorded_at)
            ).mappings().all()
        conclusions = [_to_conclusion(row) for row in rows]
        conclusions.sort(key=lambda c: (c.concluded_at, c.recorded_at, c.id.value))
        return conclusions


def _to_row(conclusion: Conclusion) -> dict[str, Any]:
    return {
        "conclusion_id": str(conclusion.id),
        "evidence_id": str(conclusion.evidence_id),
        "statement": conclusion.statement.value,
        "note": conclusion.note,
        "concluded_at": conclusion.concluded_at.isoformat(),
        "recorded_at": conclusion.recorded_at.isoformat(),
    }


def _to_conclusion(row: Mapping[str, Any]) -> Conclusion:
    return Conclusion(
        id=ConclusionId(uuid.UUID(row["conclusion_id"])),
        evidence_id=EvidenceId(uuid.UUID(row["evidence_id"])),
        statement=Statement(row["statement"]),
        concluded_at=datetime.fromisoformat(row["concluded_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        note=row["note"],
    )
