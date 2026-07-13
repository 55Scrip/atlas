"""Repository interface for the Outcome aggregate.

Insert-only: no update, no delete. No SQL foreign key on decision_id
(matching the rest of this codebase's convention).
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.value_objects import OutcomeId


class OutcomeRepository(Protocol):
    def add(self, outcome: Outcome) -> None:
        """Insert a new Outcome."""
        ...

    def get(self, outcome_id: OutcomeId) -> Outcome | None:
        """Return a single Outcome by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Outcome]:
        """Return every Outcome ever recorded, in chronological order:
        occurred_at ascending, then recorded_at, then id as tie-breaker.
        """
        ...

    def list_by_decision_id(self, decision_id: DecisionId) -> list[Outcome]:
        """Return every Outcome recorded for a given Decision.

        No uniqueness: a Decision may accrue more than one Outcome entry
        over time.
        """
        ...
