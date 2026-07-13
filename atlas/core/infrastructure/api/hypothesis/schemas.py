"""HTTP request/response schemas for Hypothesis Capture (API-004).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`;
Python attribute names stay snake_case. Built camelCase-first — there is
no prior snake_case version of this API to migrate away from.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateHypothesisRequest(CamelModel):
    statement: str
    formulated_at: datetime
    note: str | None = None


class HypothesisResponse(CamelModel):
    hypothesis_id: uuid.UUID
    statement: str
    note: str | None
    formulated_at: datetime
    recorded_at: datetime

    @classmethod
    def from_domain(cls, hypothesis: Hypothesis) -> HypothesisResponse:
        return cls(
            hypothesis_id=hypothesis.id.value,
            statement=hypothesis.statement.value,
            note=hypothesis.note,
            formulated_at=hypothesis.formulated_at,
            recorded_at=hypothesis.recorded_at,
        )
