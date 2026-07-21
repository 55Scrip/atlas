"""Application service for the Decision Capture use case (API-001).

This is the one place raw, untrusted input (primitives from an HTTP request,
a CLI command, an import job) is translated into the Decision aggregate. It
holds no business rules of its own — those live on Decision and its value
objects — it only wires translation and persistence together.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)


@dataclass(frozen=True)
class CaptureDecisionRequest:
    case_id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    subject: str
    reason: str
    confidence: int
    decided_at: datetime | None = None
    source: str = DecisionSource.MANUAL.value


class CaptureDecisionService:
    def __init__(self, repository: DecisionRepository) -> None:
        self._repository = repository

    def capture(self, request: CaptureDecisionRequest) -> Decision:
        decision = Decision.register(
            case_id=CaseId(request.case_id),
            user_id=UserId(request.user_id),
            decision_type=DecisionType.coerce(request.decision_type),
            subject=Subject(request.subject),
            investment_case=InvestmentCase(request.reason),
            confidence=Confidence(request.confidence),
            decided_at=request.decided_at,
            source=DecisionSource(request.source),
        )
        self._repository.add(decision)
        return decision
