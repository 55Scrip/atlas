"""Application service for the Evidence Capture use case (API-005).

Like HypothesisService, this needs only one repository and no
cross-aggregate existence/uniqueness checks: Evidence introduces no
relationship to any other aggregate. This service owns all three use
cases the spec asks for: capture, retrieve by id, retrieve all.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement


@dataclass(frozen=True)
class CaptureEvidenceRequest:
    statement: str
    direction: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


class EvidenceService:
    def __init__(self, repository: EvidenceRepository) -> None:
        self._repository = repository

    def capture(self, request: CaptureEvidenceRequest) -> Evidence:
        evidence = Evidence.capture(
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
