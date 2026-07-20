"""HTTP request/response schemas for Knowledge Reference (DO-IMP-003).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`.
The target reference embeds the shared `TypedDomainObjectReferenceSchema`
(DO-IMP-002) directly, rather than re-declaring `targetType`/`targetId`
as flat fields — this is that schema's own stated purpose: letting each
owning Domain Object's API embed it without reinventing camelCase
target-reference serialization.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.core.infrastructure.api.shared.typed_reference_schemas import (
    TypedDomainObjectReferenceSchema,
)


class CreateKnowledgeReferenceRequest(CamelModel):
    case_id: uuid.UUID
    target: TypedDomainObjectReferenceSchema


class KnowledgeReferenceResponse(CamelModel):
    knowledge_reference_id: uuid.UUID
    case_id: uuid.UUID
    target: TypedDomainObjectReferenceSchema
    recorded_at: datetime

    @classmethod
    def from_domain(cls, knowledge_reference: KnowledgeReference) -> KnowledgeReferenceResponse:
        return cls(
            knowledge_reference_id=knowledge_reference.id.value,
            case_id=knowledge_reference.case_id.value,
            target=TypedDomainObjectReferenceSchema.from_domain(knowledge_reference.target),
            recorded_at=knowledge_reference.recorded_at,
        )
