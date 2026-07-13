"""Application service for the Learning use case (ATLAS-001 Core Loop).

Verifies the referenced Evaluation exists (a pure read against
EvaluationRepository) before constructing the new Learning, reusing
Evaluation's own existing EvaluationNotFoundError rather than defining a
duplicate. Never writes to EvaluationRepository. Learning is the
terminal node of the Core Loop — nothing downstream reuses its own
LearningNotFoundError.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.evaluation.exceptions import EvaluationNotFoundError
from atlas.core.domain.evaluation.repository import EvaluationRepository
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.learning.exceptions import LearningNotFoundError
from atlas.core.domain.learning.repository import LearningRepository
from atlas.core.domain.learning.value_objects import LearningId, Statement


@dataclass(frozen=True)
class CaptureLearningRequest:
    evaluation_id: uuid.UUID
    statement: str
    learned_at: datetime
    note: str | None = None


class LearningService:
    def __init__(
        self,
        evaluation_repository: EvaluationRepository,
        learning_repository: LearningRepository,
    ) -> None:
        self._evaluations = evaluation_repository
        self._learnings = learning_repository

    def capture(self, request: CaptureLearningRequest) -> Learning:
        evaluation_id = EvaluationId(request.evaluation_id)

        if self._evaluations.get(evaluation_id) is None:
            raise EvaluationNotFoundError(f"No Evaluation found with id {evaluation_id}")

        learning = Learning.capture(
            evaluation_id=evaluation_id,
            statement=Statement(request.statement),
            learned_at=request.learned_at,
            note=request.note,
        )
        self._learnings.add(learning)
        return learning

    def get(self, learning_id: LearningId) -> Learning:
        learning = self._learnings.get(learning_id)
        if learning is None:
            raise LearningNotFoundError(f"No Learning found with id {learning_id}")
        return learning

    def list_all(self) -> list[Learning]:
        return self._learnings.list_all()
