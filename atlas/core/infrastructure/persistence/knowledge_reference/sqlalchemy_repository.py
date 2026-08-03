"""SQLAlchemy-backed KnowledgeReferenceRepository.

`add` is the only insert operation and is always an INSERT. No foreign
keys, no uniqueness constraint beyond the primary key — duplicate
targets across separate Knowledge References are permitted (OE-002
§5.2 states no restriction against it).

Atlas Alpha, Knowledge Reference Sprint 1: `list_all` and `delete` are
new, mirroring Evidence's own identical additions in Evidence Sprint 1.
`delete` is a plain DELETE by primary key, idempotent (deleting an
already-absent id affects zero rows without error).
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.domain.shared.domain_object_type import DomainObjectType
from atlas.core.domain.shared.typed_reference import TypedDomainObjectReference
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    knowledge_references_table,
)


class SqlAlchemyKnowledgeReferenceRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, knowledge_reference: KnowledgeReference) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                insert(knowledge_references_table).values(**_to_row(knowledge_reference))
            )

    def get(self, knowledge_reference_id: KnowledgeReferenceId) -> KnowledgeReference | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(knowledge_references_table).where(
                        knowledge_references_table.c.knowledge_reference_id
                        == str(knowledge_reference_id)
                    )
                )
                .mappings()
                .first()
            )
        return _to_knowledge_reference(row) if row is not None else None

    def list_all(self) -> list[KnowledgeReference]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(knowledge_references_table).order_by(
                        knowledge_references_table.c.recorded_at
                    )
                )
                .mappings()
                .all()
            )
        records = [_to_knowledge_reference(row) for row in rows]
        records.sort(key=lambda k: (k.recorded_at, k.id.value))
        return records

    def delete(self, knowledge_reference_id: KnowledgeReferenceId) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                delete(knowledge_references_table).where(
                    knowledge_references_table.c.knowledge_reference_id
                    == str(knowledge_reference_id)
                )
            )


def _to_row(knowledge_reference: KnowledgeReference) -> dict[str, Any]:
    return {
        "knowledge_reference_id": str(knowledge_reference.id),
        "case_id": str(knowledge_reference.case_id),
        "target_type": knowledge_reference.target.target_type.value,
        "target_id": str(knowledge_reference.target.target_id),
        "recorded_at": knowledge_reference.recorded_at.isoformat(),
    }


def _to_knowledge_reference(row: Mapping[str, Any]) -> KnowledgeReference:
    return KnowledgeReference(
        id=KnowledgeReferenceId(uuid.UUID(row["knowledge_reference_id"])),
        case_id=CaseId(uuid.UUID(row["case_id"])),
        target=TypedDomainObjectReference(
            target_type=DomainObjectType(row["target_type"]),
            target_id=uuid.UUID(row["target_id"]),
        ),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )
