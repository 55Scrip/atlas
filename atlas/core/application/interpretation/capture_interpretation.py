"""Application service for the Interpretation use case (ATLAS-001 Core Loop).

Unlike the six-step aggregates with no upstream dependency, this service
is where the cross-aggregate check happens: it verifies the referenced
Observation exists (a pure read against ObservationRepository) before
constructing the new Interpretation — mirroring
CaptureDecisionContextService's check against DecisionRepository. It
never writes to ObservationRepository.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.interpretation.entity import Interpretation
from atlas.core.domain.interpretation.exceptions import InterpretationNotFoundError
from atlas.core.domain.interpretation.repository import InterpretationRepository
from atlas.core.domain.interpretation.value_objects import InterpretationId, Statement
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId


class ObservationNotFoundError(Exception):
    """Raised when an Interpretation is captured against an Observation that
    does not exist.

    Defined here, not imported, because Observation (API-003) has no
    NotFoundError of its own — the same situation DecisionContext (API-002)
    was in with respect to Decision before Hypothesis/Evidence later added
    their own.
    """


@dataclass(frozen=True)
class CaptureInterpretationRequest:
    observation_id: uuid.UUID
    statement: str
    interpreted_at: datetime
    note: str | None = None


class InterpretationService:
    def __init__(
        self,
        observation_repository: ObservationRepository,
        interpretation_repository: InterpretationRepository,
    ) -> None:
        self._observations = observation_repository
        self._interpretations = interpretation_repository

    def capture(self, request: CaptureInterpretationRequest) -> Interpretation:
        observation_id = ObservationId(request.observation_id)

        if self._observations.get(observation_id) is None:
            raise ObservationNotFoundError(f"No Observation found with id {observation_id}")

        interpretation = Interpretation.capture(
            observation_id=observation_id,
            statement=Statement(request.statement),
            interpreted_at=request.interpreted_at,
            note=request.note,
        )
        self._interpretations.add(interpretation)
        return interpretation

    def get(self, interpretation_id: InterpretationId) -> Interpretation:
        interpretation = self._interpretations.get(interpretation_id)
        if interpretation is None:
            raise InterpretationNotFoundError(
                f"No Interpretation found with id {interpretation_id}"
            )
        return interpretation

    def list_all(self) -> list[Interpretation]:
        return self._interpretations.list_all()
