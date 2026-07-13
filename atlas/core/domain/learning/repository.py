"""Repository interface for the Learning aggregate.

Insert-only: no update, no delete. No SQL foreign key on evaluation_id
(matching the rest of this codebase's convention).
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.entity import Learning
from atlas.core.domain.learning.value_objects import LearningId


class LearningRepository(Protocol):
    def add(self, learning: Learning) -> None:
        """Insert a new Learning."""
        ...

    def get(self, learning_id: LearningId) -> Learning | None:
        """Return a single Learning by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Learning]:
        """Return every Learning ever captured, in chronological order:
        learned_at ascending, then recorded_at, then id as tie-breaker.
        """
        ...

    def list_by_evaluation_id(self, evaluation_id: EvaluationId) -> list[Learning]:
        """Return every Learning drawn from a given Evaluation."""
        ...
