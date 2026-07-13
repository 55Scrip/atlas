"""HTTP request/response schemas for Evidence Capture (API-005).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`;
Python attribute names stay snake_case. Built camelCase-first — there is
no prior snake_case version of this API to migrate away from.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateEvidenceRequest(CamelModel):
    statement: str
    direction: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


class EvidenceResponse(CamelModel):
    evidence_id: uuid.UUID
    statement: str
    direction: str
    source: str | None
    note: str | None
    observed_at: datetime
    recorded_at: datetime

    @classmethod
    def from_domain(cls, evidence: Evidence) -> EvidenceResponse:
        return cls(
            evidence_id=evidence.id.value,
            statement=evidence.statement.value,
            direction=evidence.direction.value,
            source=evidence.source,
            note=evidence.note,
            observed_at=evidence.observed_at,
            recorded_at=evidence.recorded_at,
        )
