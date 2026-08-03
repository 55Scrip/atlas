"""Repository interface for the Evidence aggregate.

No SQL foreign key on observation_id (matching Interpretation's own
convention and the rest of this codebase) — existence of the referenced
Observation is checked by the application service, not by a database
constraint.

Atlas Alpha, Evidence Sprint 1: `delete` is new — the first delete
capability in this codebase's persistence layer. Evidence remains
otherwise insert-only, like Decision's, DecisionContext's, Observation's,
and Hypothesis's: no update, no patch.
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

    def delete(self, evidence_id: EvidenceId) -> None:
        """Remove an Evidence record by id. Idempotent: deleting an id
        that does not exist (already deleted, or never existed) is not
        an error at this layer — existence is the application service's
        concern (see `EvidenceService.delete`), the same division of
        responsibility already used for `get`.
        """
        ...
