"""HTTP request/response schemas for Observation Capture (API-003).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`;
Python attribute names stay snake_case.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.observation.entity import Observation
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateObservationRequest(CamelModel):
    subject: str
    statement: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


class ObservationResponse(CamelModel):
    observation_id: uuid.UUID
    subject: str
    statement: str
    source: str | None
    note: str | None
    observed_at: datetime
    recorded_at: datetime

    @classmethod
    def from_domain(cls, observation: Observation) -> ObservationResponse:
        return cls(
            observation_id=observation.id.value,
            subject=observation.subject.value,
            statement=observation.statement.value,
            source=observation.source,
            note=observation.note,
            observed_at=observation.observed_at,
            recorded_at=observation.recorded_at,
        )
