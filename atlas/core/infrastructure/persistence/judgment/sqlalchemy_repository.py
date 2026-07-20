"""SQLAlchemy-backed JudgmentRepository.

`add` is the only write operation and is always an INSERT. No foreign
keys, no uniqueness constraint beyond the primary key — duplicate
subject references across separate Judgments are permitted (OE-002
§5.4 states no restriction against it), and content-identical
Judgments remain distinct by identity (Judgment-Implementation-Design.md
Section 13).
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.value_objects import Characterization, JudgmentId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.judgment.table import judgments_table


class SqlAlchemyJudgmentRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, judgment: Judgment) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(judgments_table).values(**_to_row(judgment)))

    def get(self, judgment_id: JudgmentId) -> Judgment | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(judgments_table).where(
                        judgments_table.c.judgment_id == str(judgment_id)
                    )
                )
                .mappings()
                .first()
            )
        return _to_judgment(row) if row is not None else None


def _to_row(judgment: Judgment) -> dict[str, Any]:
    subject = judgment.subject
    return {
        "judgment_id": str(judgment.id),
        "case_id": str(judgment.case_id),
        "characterization": str(judgment.characterization),
        "subject_target_type": subject.target_type.value if subject is not None else None,
        "subject_target_id": str(subject.target_id) if subject is not None else None,
        "recorded_at": judgment.recorded_at.isoformat(),
    }


def _to_judgment(row: Mapping[str, Any]) -> Judgment:
    subject: TypedDomainObjectReference | None = None
    if row["subject_target_type"] is not None:
        subject = TypedDomainObjectReference(
            target_type=DomainObjectType(row["subject_target_type"]),
            target_id=uuid.UUID(row["subject_target_id"]),
        )
    return Judgment(
        id=JudgmentId(uuid.UUID(row["judgment_id"])),
        case_id=CaseId(uuid.UUID(row["case_id"])),
        characterization=Characterization(row["characterization"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        subject=subject,
    )
