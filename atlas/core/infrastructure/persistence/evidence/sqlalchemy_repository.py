"""SQLAlchemy-backed EvidenceRepository.

`add` is the only insert operation and is always an INSERT. No foreign
keys, no uniqueness constraint beyond the primary key — Evidence has no
cross-aggregate invariant enforced at the database layer (the referenced
Observation's existence is checked by the application service).

Atlas Alpha, Evidence Sprint 1: `delete` is new — a plain DELETE by
primary key, idempotent (deleting an already-absent id affects zero rows
without error), matching the repository interface's own contract.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.evidence.table import evidence_table


class SqlAlchemyEvidenceRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, evidence: Evidence) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(evidence_table).values(**_to_row(evidence)))

    def get(self, evidence_id: EvidenceId) -> Evidence | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(evidence_table).where(evidence_table.c.evidence_id == str(evidence_id))
            ).mappings().first()
        return _to_evidence(row) if row is not None else None

    def delete(self, evidence_id: EvidenceId) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                delete(evidence_table).where(evidence_table.c.evidence_id == str(evidence_id))
            )

    def list_all(self) -> list[Evidence]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(evidence_table).order_by(evidence_table.c.recorded_at)
            ).mappings().all()
        records = [_to_evidence(row) for row in rows]
        # observed_at preserves its investor-supplied offset (not
        # normalized to UTC), so a text-based ORDER BY on that column
        # would not reflect true chronological order across mixed
        # offsets. Sort here instead, comparing tz-aware datetimes (which
        # compare by absolute instant regardless of stored offset) —
        # observed_at ascending, then recorded_at, then evidence_id as
        # the deterministic final tie-breaker.
        records.sort(key=lambda e: (e.observed_at, e.recorded_at, e.id.value))
        return records


def _to_row(evidence: Evidence) -> dict[str, Any]:
    return {
        "evidence_id": str(evidence.id),
        "observation_id": str(evidence.observation_id),
        "statement": evidence.statement.value,
        "direction": evidence.direction.value,
        "source": evidence.source,
        "note": evidence.note,
        "observed_at": evidence.observed_at.isoformat(),
        "recorded_at": evidence.recorded_at.isoformat(),
    }


def _to_evidence(row: Mapping[str, Any]) -> Evidence:
    return Evidence(
        id=EvidenceId(uuid.UUID(row["evidence_id"])),
        observation_id=ObservationId(uuid.UUID(row["observation_id"])),
        statement=Statement(row["statement"]),
        direction=Direction(row["direction"]),
        observed_at=datetime.fromisoformat(row["observed_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        source=row["source"],
        note=row["note"],
    )
