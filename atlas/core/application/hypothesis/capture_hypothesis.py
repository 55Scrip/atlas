"""Application service for the Hypothesis Capture use case (API-004).

Like CaptureObservationService, this needs only one repository and no
cross-aggregate existence/uniqueness checks: Hypothesis introduces no
relationship to any other aggregate. Unlike API-003, this service also
owns the retrieve-by-id and retrieve-all use cases, per this increment's
own spec.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.hypothesis.exceptions import HypothesisNotFoundError
from atlas.core.domain.hypothesis.repository import HypothesisRepository
from atlas.core.domain.hypothesis.value_objects import HypothesisId, Statement


@dataclass(frozen=True)
class CaptureHypothesisRequest:
    statement: str
    formulated_at: datetime
    note: str | None = None


class HypothesisService:
    def __init__(self, repository: HypothesisRepository) -> None:
        self._repository = repository

    def capture(self, request: CaptureHypothesisRequest) -> Hypothesis:
        hypothesis = Hypothesis.capture(
            statement=Statement(request.statement),
            formulated_at=request.formulated_at,
            note=request.note,
        )
        self._repository.add(hypothesis)
        return hypothesis

    def get(self, hypothesis_id: HypothesisId) -> Hypothesis:
        hypothesis = self._repository.get(hypothesis_id)
        if hypothesis is None:
            raise HypothesisNotFoundError(f"No Hypothesis found with id {hypothesis_id}")
        return hypothesis

    def list_all(self) -> list[Hypothesis]:
        return self._repository.list_all()
