"""Application service for the Observation Capture use case (API-003).

Unlike CaptureDecisionContextService, this needs only one repository and
no cross-aggregate existence/uniqueness checks: Observation introduces no
relationship to any other aggregate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import Statement, Subject


@dataclass(frozen=True)
class CaptureObservationRequest:
    subject: str
    statement: str
    observed_at: datetime
    source: str | None = None
    note: str | None = None


class CaptureObservationService:
    def __init__(self, repository: ObservationRepository) -> None:
        self._repository = repository

    def capture(self, request: CaptureObservationRequest) -> Observation:
        observation = Observation.capture(
            subject=Subject(request.subject),
            statement=Statement(request.statement),
            observed_at=request.observed_at,
            source=request.source,
            note=request.note,
        )
        self._repository.add(observation)
        return observation
