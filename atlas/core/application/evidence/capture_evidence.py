"""Application service for the Evidence Capture use case (API-005).

Atlas Alpha, Evidence Sprint 1: this is now where the cross-aggregate
check happens — it verifies the referenced Observation exists (a pure
read against ObservationRepository) before constructing the new
Evidence, mirroring CaptureDecisionContextService's check against
DecisionRepository and InterpretationService's identical check for the
same relationship. It never writes to ObservationRepository. This
service owns all four use cases now in scope: capture, retrieve by id,
retrieve all, delete.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError, ObservationNotFoundError
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId


@dataclass(frozen=True)
class CaptureEvidenceRequest:
    observation_id: uuid.UUID
    statement: str
    direction: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


class EvidenceService:
    def __init__(
        self,
        observation_repository: ObservationRepository,
        evidence_repository: EvidenceRepository,
    ) -> None:
        self._observations = observation_repository
        self._repository = evidence_repository

    def capture(self, request: CaptureEvidenceRequest) -> Evidence:
        observation_id = ObservationId(request.observation_id)

        if self._observations.get(observation_id) is None:
            raise ObservationNotFoundError(f"No Observation found with id {observation_id}")

        evidence = Evidence.capture(
            observation_id=observation_id,
            statement=Statement(request.statement),
            direction=Direction.coerce(request.direction),
            observed_at=request.observed_at,
            source=request.source,
            note=request.note,
        )
        self._repository.add(evidence)
        return evidence

    def get(self, evidence_id: EvidenceId) -> Evidence:
        evidence = self._repository.get(evidence_id)
        if evidence is None:
            raise EvidenceNotFoundError(f"No Evidence found with id {evidence_id}")
        return evidence

    def list_all(self) -> list[Evidence]:
        return self._repository.list_all()

    def delete(self, evidence_id: EvidenceId) -> None:
        if self._repository.get(evidence_id) is None:
            raise EvidenceNotFoundError(f"No Evidence found with id {evidence_id}")
        self._repository.delete(evidence_id)
