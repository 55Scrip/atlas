"""HTTP request/response schemas for Decision Capture.

These are transport-layer contracts, deliberately separate from the domain's
value objects: the wire format (JSON, UUID-as-string) is an HTTP concern, not
a business rule, and the two are free to diverge without touching the
domain. Per ADR-004, the wire format is camelCase (`CamelModel`); Python
attribute names below stay snake_case, matching the domain and every other
internal layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.decision.entity import Decision
from atlas.core.infrastructure.api.serialization import CamelModel

ATLAS_LEARNING_MESSAGE = (
    "Atlas has recorded your decision. It has started learning, but does not "
    "yet understand your decision patterns."
)


class CreateDecisionRequest(CamelModel):
    case_id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    subject: str
    reason: str
    confidence: int
    decided_at: datetime | None = None
    source: str = "Manual"
    observation_id: uuid.UUID | None = None


class DecisionSummary(CamelModel):
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    subject: str
    reason: str
    confidence: int
    decided_at: datetime
    recorded_at: datetime
    source: str
    observation_id: uuid.UUID | None = None

    @classmethod
    def from_domain(cls, decision: Decision) -> DecisionSummary:
        return cls(
            id=decision.id.value,
            case_id=decision.case_id.value,
            user_id=decision.user_id.value,
            decision_type=decision.decision_type.value,
            subject=decision.subject.value,
            reason=decision.investment_case.reason,
            confidence=decision.confidence.value,
            decided_at=decision.decided_at,
            recorded_at=decision.recorded_at,
            source=decision.source.value,
            observation_id=(
                decision.observation_id.value if decision.observation_id is not None else None
            ),
        )


class DecisionCreatedResponse(DecisionSummary):
    message: str = ATLAS_LEARNING_MESSAGE
