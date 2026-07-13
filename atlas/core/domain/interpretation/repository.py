"""Repository interface for the Interpretation aggregate.

Insert-only: no update, no delete. No SQL foreign key on observation_id
(matching the rest of this codebase's convention) — existence of the
referenced Observation is checked by the application service, not by a
database constraint.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.interpretation.entity import Interpretation
from atlas.core.domain.interpretation.value_objects import InterpretationId
from atlas.core.domain.observation.value_objects import ObservationId


class InterpretationRepository(Protocol):
    def add(self, interpretation: Interpretation) -> None:
        """Insert a new Interpretation."""
        ...

    def get(self, interpretation_id: InterpretationId) -> Interpretation | None:
        """Return a single Interpretation by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Interpretation]:
        """Return every Interpretation ever captured, in chronological order:
        interpreted_at ascending, then recorded_at, then id as tie-breaker.
        """
        ...

    def list_by_observation_id(self, observation_id: ObservationId) -> list[Interpretation]:
        """Return every Interpretation of a given Observation.

        No uniqueness: one Observation may have zero, one, or many
        Interpretations over time.
        """
        ...
