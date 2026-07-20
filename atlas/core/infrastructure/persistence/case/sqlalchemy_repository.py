"""SQLAlchemy-backed CaseRepository.

`add` is the only write operation and is always an INSERT. No foreign
keys, no uniqueness constraint beyond the primary key — Case has no
cross-aggregate invariant to enforce.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.entity import Case
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.persistence.case.table import cases_table


class SqlAlchemyCaseRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, case: Case) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(cases_table).values(**_to_row(case)))

    def get(self, case_id: CaseId) -> Case | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(cases_table).where(cases_table.c.case_id == str(case_id))
            ).mappings().first()
        return _to_case(row) if row is not None else None


def _to_row(case: Case) -> dict[str, Any]:
    return {
        "case_id": str(case.id),
        "recorded_at": case.recorded_at.isoformat(),
    }


def _to_case(row: Mapping[str, Any]) -> Case:
    return Case(
        id=CaseId(uuid.UUID(row["case_id"])),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )
