"""HTTP request/response schemas for Decision Capture.

These are transport-layer contracts, deliberately separate from the domain's
value objects: the wire format (JSON, UUID-as-string) is an HTTP concern, not
a business rule, and the two are free to diverge without touching the
domain.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from atlas.core.domain.decision.entity import Decision

ATLAS_LEARNING_MESSAGE = (
    "Atlas has recorded your decision. It has started learning, but does not "
    "yet understand your decision patterns."
)


class CreateDecisionRequest(BaseModel):
    user_id: uuid.UUID
    decision_type: str
    subject: str
    reason: str
    confidence: int
    decided_at: datetime | None = None
    source: str = "Manual"


class DecisionSummary(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    subject: str
    reason: str
    confidence: int
    decided_at: datetime
    recorded_at: datetime
    source: str

    @classmethod
    def from_domain(cls, decision: Decision) -> DecisionSummary:
        return cls(
            id=decision.id.value,
            user_id=decision.user_id.value,
            decision_type=decision.decision_type.value,
            subject=decision.subject.value,
            reason=decision.investment_case.reason,
            confidence=decision.confidence.value,
            decided_at=decision.decided_at,
            recorded_at=decision.recorded_at,
            source=decision.source.value,
        )


class DecisionCreatedResponse(DecisionSummary):
    message: str = ATLAS_LEARNING_MESSAGE
