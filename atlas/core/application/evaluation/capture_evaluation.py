"""Application service for the Evaluation use case (ATLAS-001 Core Loop).

Verifies the referenced Outcome exists (a pure read against
OutcomeRepository) before constructing the new Evaluation, reusing
Outcome's own existing OutcomeNotFoundError rather than defining a
duplicate. Never writes to OutcomeRepository.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.exceptions import EvaluationNotFoundError
from atlas.core.domain.evaluation.repository import EvaluationRepository
from atlas.core.domain.evaluation.value_objects import EvaluationId, Statement
from atlas.core.domain.outcome.exceptions import OutcomeNotFoundError
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.outcome.value_objects import OutcomeId


@dataclass(frozen=True)
class CaptureEvaluationRequest:
    outcome_id: uuid.UUID
    statement: str
    evaluated_at: datetime
    note: str | None = None


class EvaluationService:
    def __init__(
        self,
        outcome_repository: OutcomeRepository,
        evaluation_repository: EvaluationRepository,
    ) -> None:
        self._outcomes = outcome_repository
        self._evaluations = evaluation_repository

    def capture(self, request: CaptureEvaluationRequest) -> Evaluation:
        outcome_id = OutcomeId(request.outcome_id)

        if self._outcomes.get(outcome_id) is None:
            raise OutcomeNotFoundError(f"No Outcome found with id {outcome_id}")

        evaluation = Evaluation.capture(
            outcome_id=outcome_id,
            statement=Statement(request.statement),
            evaluated_at=request.evaluated_at,
            note=request.note,
        )
        self._evaluations.add(evaluation)
        return evaluation

    def get(self, evaluation_id: EvaluationId) -> Evaluation:
        evaluation = self._evaluations.get(evaluation_id)
        if evaluation is None:
            raise EvaluationNotFoundError(f"No Evaluation found with id {evaluation_id}")
        return evaluation

    def list_all(self) -> list[Evaluation]:
        return self._evaluations.list_all()
