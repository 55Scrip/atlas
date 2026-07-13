"""Repository interface for the DecisionContext aggregate.

Insert-only, like Decision's: there is no update and no delete method, so
"never replace historical context" is enforced by the interface shape, not
by convention.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.entity import DecisionContext


class DecisionContextRepository(Protocol):
    def add(self, context: DecisionContext) -> None:
        """Insert a new DecisionContext.

        Raises DuplicateDecisionContextError if the referenced Decision
        already has one — at most one DecisionContext per Decision.
        """
        ...

    def get_by_decision_id(self, decision_id: DecisionId) -> DecisionContext | None:
        """Return the DecisionContext for a Decision, or None if none exists yet."""
        ...
