"""Repository interface for the ReflectionResponse aggregate.

Insert-only: no update, no delete. No SQL foreign key on decision_id
(matching the rest of this codebase's convention).
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.value_objects import ReflectionResponseId


class ReflectionResponseRepository(Protocol):
    def add(self, reflection_response: ReflectionResponse) -> None:
        """Insert a new ReflectionResponse."""
        ...

    def get(self, reflection_response_id: ReflectionResponseId) -> ReflectionResponse | None:
        """Return a single ReflectionResponse by id, or None if it does not exist."""
        ...
