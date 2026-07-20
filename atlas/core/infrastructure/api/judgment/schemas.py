"""HTTP request/response schemas for Judgment (DO-IMP-004).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`.
The subject reference embeds the shared `TypedDomainObjectReferenceSchema`
(DO-IMP-002) directly, as an optional nested `subject` field, rather
than re-declaring `subjectTargetType`/`subjectTargetId` as flat
optional fields — this keeps the pairing (both present or both absent)
structural, not something Pydantic validation must separately enforce.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.judgment.entity import Judgment
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.core.infrastructure.api.shared.typed_reference_schemas import (
    TypedDomainObjectReferenceSchema,
)


class CreateJudgmentRequest(CamelModel):
    case_id: uuid.UUID
    characterization: str
    subject: TypedDomainObjectReferenceSchema | None = None


class JudgmentResponse(CamelModel):
    judgment_id: uuid.UUID
    case_id: uuid.UUID
    characterization: str
    subject: TypedDomainObjectReferenceSchema | None
    recorded_at: datetime

    @classmethod
    def from_domain(cls, judgment: Judgment) -> JudgmentResponse:
        return cls(
            judgment_id=judgment.id.value,
            case_id=judgment.case_id.value,
            characterization=str(judgment.characterization),
            subject=(
                TypedDomainObjectReferenceSchema.from_domain(judgment.subject)
                if judgment.subject is not None
                else None
            ),
            recorded_at=judgment.recorded_at,
        )
