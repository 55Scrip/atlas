"""HTTP request/response schemas for Reasoning Trace (DO-IMP-009).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`.
`supports` embeds the shared `TypedDomainObjectReferenceSchema`
(DO-IMP-002) per set member, exactly as Knowledge Reference already does
for its own single target.

**JSON array ordering carries no semantic meaning** (docs/
atlas_domain_object_architecture/Reasoning-Trace-Implementation-Design.md,
Section 12, Section 31) — the domain and persistence layers treat
`supports` as a set throughout; the array shape exists only because
JSON has no native set literal. Non-emptiness (INV-013) is enforced by
`ReasoningTraceService.capture()`, not by a schema-level length
constraint — the same "structural shape here, business rule at the
service" split already used for Knowledge Reference's own required
fields.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.reasoning_trace.entity import ReasoningTrace
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.core.infrastructure.api.shared.typed_reference_schemas import (
    TypedDomainObjectReferenceSchema,
)


class CreateReasoningTraceRequest(CamelModel):
    case_id: uuid.UUID
    supports: list[TypedDomainObjectReferenceSchema]


class ReasoningTraceResponse(CamelModel):
    reasoning_trace_id: uuid.UUID
    case_id: uuid.UUID
    supports: list[TypedDomainObjectReferenceSchema]
    recorded_at: datetime

    @classmethod
    def from_domain(cls, reasoning_trace: ReasoningTrace) -> ReasoningTraceResponse:
        return cls(
            reasoning_trace_id=reasoning_trace.id.value,
            case_id=reasoning_trace.case_id.value,
            supports=[
                TypedDomainObjectReferenceSchema.from_domain(support)
                for support in reasoning_trace.supports
            ],
            recorded_at=reasoning_trace.recorded_at,
        )
