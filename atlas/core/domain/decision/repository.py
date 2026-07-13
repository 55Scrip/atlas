"""Repository interface for the Decision aggregate.

Decision history is immutable: there is only ever an insert. This interface
has no update method by design — that is not an omission to fill in later,
it is how the "no UPDATE, ever" persistence rule is enforced at the type
level.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import DecisionId


class DecisionRepository(Protocol):
    def add(self, decision: Decision) -> None:
        """Insert a new Decision. Never raises on a duplicate business state;
        Decisions are only ever new."""
        ...

    def get(self, decision_id: DecisionId) -> Decision | None:
        """Return a single Decision by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Decision]:
        """Return every Decision ever recorded, oldest first."""
        ...
