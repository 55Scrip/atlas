"""Composite application service: Decision committed from a Conclusion
(ATLAS-001 Core Loop, step 7 of 10).

Verifies the referenced Conclusion exists, then reuses the existing,
unmodified CaptureDecisionService to construct the Decision, and records
the ConclusionDecisionLink atomically. Never writes to
ConclusionRepository or modifies Decision's own construction path.

Necessarily a heavier request than the other three composite services:
Decision.register() requires user_id, decision_type, subject,
investment_case, and confidence, none of which are derivable from a
Conclusion — this is a consequence of Decision's existing required
fields, not scope creep introduced here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.domain.conclusion.exceptions import ConclusionNotFoundError
from atlas.core.domain.conclusion.repository import ConclusionRepository
from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import DecisionSource
from atlas.core.domain.reasoning_link.entity import ConclusionDecisionLink
from atlas.core.domain.reasoning_link.repository import ConclusionDecisionLinkRepository


@dataclass(frozen=True)
class CommitDecisionFromConclusionRequest:
    conclusion_id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    subject: str
    reason: str
    confidence: int
    decided_at: datetime | None = None
    source: str = DecisionSource.MANUAL.value


@dataclass(frozen=True)
class CommitDecisionFromConclusionResult:
    decision: Decision
    link: ConclusionDecisionLink


class CommitDecisionFromConclusionService:
    def __init__(
        self,
        conclusion_repository: ConclusionRepository,
        decision_service: CaptureDecisionService,
        link_repository: ConclusionDecisionLinkRepository,
    ) -> None:
        self._conclusions = conclusion_repository
        self._decision_service = decision_service
        self._links = link_repository

    def commit(
        self, request: CommitDecisionFromConclusionRequest
    ) -> CommitDecisionFromConclusionResult:
        conclusion_id = ConclusionId(request.conclusion_id)

        if self._conclusions.get(conclusion_id) is None:
            raise ConclusionNotFoundError(f"No Conclusion found with id {conclusion_id}")

        decision = self._decision_service.capture(
            CaptureDecisionRequest(
                user_id=request.user_id,
                decision_type=request.decision_type,
                subject=request.subject,
                reason=request.reason,
                confidence=request.confidence,
                decided_at=request.decided_at,
                source=request.source,
            )
        )
        link = ConclusionDecisionLink.capture(
            conclusion_id=conclusion_id, decision_id=decision.id
        )
        self._links.add(link)
        return CommitDecisionFromConclusionResult(decision=decision, link=link)
