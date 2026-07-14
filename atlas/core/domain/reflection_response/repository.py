"""Repository interface for the ReflectionResponse aggregate.

Insert-only: no update, no delete. No SQL foreign key on decision_id
(matching the rest of this codebase's convention).
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId


class ReflectionResponseRepository(Protocol):
    def add(self, reflection_response: ReflectionResponse) -> None:
        """Insert a new ReflectionResponse."""
        ...

    def get(self, reflection_response_id: ReflectionResponseId) -> ReflectionResponse | None:
        """Return a single ReflectionResponse by id, or None if it does not exist."""
        ...

    def list_all_for_owner(self, user_id: UserId) -> list[ReflectionResponse]:
        """Return every ReflectionResponse anchored to a Decision owned by
        this investor. Read-only; unordered — callers own final ordering,
        never trust repository or SQL row order (ATLAS-010)."""
        ...
