"""Repository interface for the Observation aggregate.

Insert-only, like Decision's and DecisionContext's: no update, no delete.
No foreign keys to any other aggregate — Observation introduces no
relationships.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.observation.entity import Observation
from atlas.core.domain.observation.value_objects import ObservationId


class ObservationRepository(Protocol):
    def add(self, observation: Observation) -> None:
        """Insert a new Observation."""
        ...

    def get(self, observation_id: ObservationId) -> Observation | None:
        """Return a single Observation by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Observation]:
        """Return every Observation ever recorded, oldest RecordedAt first."""
        ...
