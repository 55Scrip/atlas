"""Application service for the Conclusion use case (ATLAS-001 Core Loop).

Verifies the referenced Evidence exists (a pure read against
EvidenceRepository) before constructing the new Conclusion, reusing
Evidence's own existing EvidenceNotFoundError rather than defining a
duplicate — Evidence (API-005) already has one for its own .get() use
case. Never writes to EvidenceRepository.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.conclusion.entity import Conclusion
from atlas.core.domain.conclusion.exceptions import ConclusionNotFoundError
from atlas.core.domain.conclusion.repository import ConclusionRepository
from atlas.core.domain.conclusion.value_objects import ConclusionId, Statement
from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError
from atlas.core.domain.evidence.repository import EvidenceRepository
from atlas.core.domain.evidence.value_objects import EvidenceId


@dataclass(frozen=True)
class CaptureConclusionRequest:
    evidence_id: uuid.UUID
    statement: str
    concluded_at: datetime
    note: str | None = None


class ConclusionService:
    def __init__(
        self,
        evidence_repository: EvidenceRepository,
        conclusion_repository: ConclusionRepository,
    ) -> None:
        self._evidence = evidence_repository
        self._conclusions = conclusion_repository

    def capture(self, request: CaptureConclusionRequest) -> Conclusion:
        evidence_id = EvidenceId(request.evidence_id)

        if self._evidence.get(evidence_id) is None:
            raise EvidenceNotFoundError(f"No Evidence found with id {evidence_id}")

        conclusion = Conclusion.capture(
            evidence_id=evidence_id,
            statement=Statement(request.statement),
            concluded_at=request.concluded_at,
            note=request.note,
        )
        self._conclusions.add(conclusion)
        return conclusion

    def get(self, conclusion_id: ConclusionId) -> Conclusion:
        conclusion = self._conclusions.get(conclusion_id)
        if conclusion is None:
            raise ConclusionNotFoundError(f"No Conclusion found with id {conclusion_id}")
        return conclusion

    def list_all(self) -> list[Conclusion]:
        return self._conclusions.list_all()
