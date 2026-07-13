"""Repository interface for the Evidence aggregate.

Insert-only, like Decision's, DecisionContext's, Observation's, and
Hypothesis's: no update, no delete. No foreign keys to any other
aggregate — Evidence introduces no relationships.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.evidence.entity import Evidence
from atlas.core.domain.evidence.value_objects import EvidenceId


class EvidenceRepository(Protocol):
    def add(self, evidence: Evidence) -> None:
        """Insert a new Evidence record."""
        ...

    def get(self, evidence_id: EvidenceId) -> Evidence | None:
        """Return a single Evidence record by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[Evidence]:
        """Return every Evidence record ever captured, in chronological
        order: observed_at ascending, then recorded_at ascending, then
        evidence_id as a deterministic final tie-breaker.
        """
        ...
