"""Repository interface for the Evaluation aggregate.

Insert-only: no update, no delete. No SQL foreign key on outcome_id
(matching the rest of this codebase's convention).
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.evaluation.entity import Evaluation
from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.outcome.value_objects import OutcomeId


class EvaluationRepository(Protocol):
    def add(self, evaluation: Evaluation) -> None:
        """Insert a new Evaluation."""
        ...

    def get(self, evaluation_id: EvaluationId) -> Evaluation | None:
        """Return a single Evaluation by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Evaluation]:
        """Return every Evaluation ever captured, in chronological order:
        evaluated_at ascending, then recorded_at, then id as tie-breaker.
        """
        ...

    def list_by_outcome_id(self, outcome_id: OutcomeId) -> list[Evaluation]:
        """Return every Evaluation of a given Outcome."""
        ...
