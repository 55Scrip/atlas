"""HTTP request/response schemas for Outcome (ATLAS-001 Core Loop).

Outcome had no REST API of any kind before Atlas Alpha's Outcome Sprint
1 (docs/atlas_domain_object_architecture/Outcome-Implementation-Design.md,
Section 42: "no atlas/core/infrastructure/api/outcome/ directory
exists"). This mirrors Decision's own schema shape exactly, since
Outcome is Decision's direct architectural sibling (both predate the
DO-IMP-00X typed-reference series and share the same plain, dedicated-
field convention) — not the Knowledge Reference/Reasoning
Trace/Judgment family. Per ADR-004, the wire format is camelCase via
the shared `CamelModel`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.outcome.entity import Outcome
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateOutcomeRequest(CamelModel):
    decision_id: uuid.UUID
    statement: str
    occurred_at: datetime
    note: str | None = None


class OutcomeResponse(CamelModel):
    id: uuid.UUID
    case_id: uuid.UUID
    decision_id: uuid.UUID
    statement: str
    note: str | None
    occurred_at: datetime
    recorded_at: datetime

    @classmethod
    def from_domain(cls, outcome: Outcome) -> OutcomeResponse:
        return cls(
            id=outcome.id.value,
            case_id=outcome.case_id.value,
            decision_id=outcome.decision_id.value,
            statement=str(outcome.statement),
            note=outcome.note,
            occurred_at=outcome.occurred_at,
            recorded_at=outcome.recorded_at,
        )
