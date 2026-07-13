"""Repository interface for the Hypothesis aggregate.

Insert-only, like Decision's, DecisionContext's, and Observation's: no
update, no delete. No foreign keys to any other aggregate — Hypothesis
introduces no relationships.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.hypothesis.entity import Hypothesis
from atlas.core.domain.hypothesis.value_objects import HypothesisId


class HypothesisRepository(Protocol):
    def add(self, hypothesis: Hypothesis) -> None:
        """Insert a new Hypothesis."""
        ...

    def get(self, hypothesis_id: HypothesisId) -> Hypothesis | None:
        """Return a single Hypothesis by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Hypothesis]:
        """Return every Hypothesis ever recorded, in chronological order:
        formulated_at ascending, then recorded_at ascending, then
        hypothesis_id as a deterministic final tie-breaker.
        """
        ...
