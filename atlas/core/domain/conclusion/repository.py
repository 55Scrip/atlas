"""Repository interface for the Conclusion aggregate.

Insert-only: no update, no delete. No SQL foreign key on evidence_id
(matching the rest of this codebase's convention).
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.conclusion.entity import Conclusion
from atlas.core.domain.conclusion.value_objects import ConclusionId
from atlas.core.domain.evidence.value_objects import EvidenceId


class ConclusionRepository(Protocol):
    def add(self, conclusion: Conclusion) -> None:
        """Insert a new Conclusion."""
        ...

    def get(self, conclusion_id: ConclusionId) -> Conclusion | None:
        """Return a single Conclusion by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Conclusion]:
        """Return every Conclusion ever drawn, in chronological order:
        concluded_at ascending, then recorded_at, then id as tie-breaker.
        """
        ...

    def list_by_evidence_id(self, evidence_id: EvidenceId) -> list[Conclusion]:
        """Return every Conclusion drawn from a given Evidence record."""
        ...
