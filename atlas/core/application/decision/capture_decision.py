"""Application service for the Decision Capture use case (API-001).

This is the one place raw, untrusted input (primitives from an HTTP request,
a CLI command, an import job) is translated into the Decision aggregate. It
holds no business rules of its own — those live on Decision and its value
objects — it only wires translation and persistence together.

Atlas Alpha, Decision Sprint 1: when `observation_id` is present, this is
now also where that cross-aggregate check happens — it verifies the
referenced Observation exists and belongs to the same Case as the
Decision being captured (a pure read against `ObservationRepository`),
mirroring `EvidenceService`'s identical existence check and the same-Case
check already established for Knowledge Reference/Reasoning
Trace/Judgment's own subject/target validation. It never writes to
`ObservationRepository`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.exceptions import (
    CrossCaseObservationError,
    ObservationNotFoundError,
)
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId


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
    observation_id: uuid.UUID | None = None


class CaptureDecisionService:
    def __init__(
        self,
        repository: DecisionRepository,
        observation_repository: ObservationRepository,
    ) -> None:
        self._repository = repository
        self._observations = observation_repository

    def capture(self, request: CaptureDecisionRequest) -> Decision:
        case_id = CaseId(request.case_id)
        observation_id: ObservationId | None = None

        if request.observation_id is not None:
            observation_id = ObservationId(request.observation_id)
            observation = self._observations.get(observation_id)
            if observation is None:
                raise ObservationNotFoundError(f"No Observation found with id {observation_id}")
            if observation.case_id != case_id:
                raise CrossCaseObservationError(
                    f"Observation {observation_id} belongs to a different Case"
                )

        decision = Decision.register(
            case_id=case_id,
            user_id=UserId(request.user_id),
            decision_type=DecisionType.coerce(request.decision_type),
            subject=Subject(request.subject),
            investment_case=InvestmentCase(request.reason),
            confidence=Confidence(request.confidence),
            decided_at=request.decided_at,
            source=DecisionSource(request.source),
            observation_id=observation_id,
        )
        self._repository.add(decision)
        return decision
