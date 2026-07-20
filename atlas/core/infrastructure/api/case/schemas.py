"""HTTP response schema for the Case API (DO-IMP-001).

Per ADR-004, the wire format is camelCase via the shared `CamelModel`.
No request schema exists: Case creation takes no semantic input at all
(OE-002 §3.1) — inventing a request field solely to avoid an empty body
would add unsupported semantics, which this package's own scope forbids.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.case.entity import Case
from atlas.core.infrastructure.api.serialization import CamelModel


class CaseResponse(CamelModel):
    case_id: uuid.UUID
    recorded_at: datetime

    @classmethod
    def from_domain(cls, case: Case) -> CaseResponse:
        return cls(case_id=case.id.value, recorded_at=case.recorded_at)
