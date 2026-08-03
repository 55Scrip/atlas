"""Repository interface for the Knowledge Reference aggregate.

Atlas Alpha, Knowledge Reference Sprint 1: `list_all` and `delete` are
new — required by this sprint's own workflow (displaying a Case's
Knowledge References, and removing one), mirroring the identical
additions already made to Evidence's own repository in Evidence Sprint
1. `update` remains unsupported, matching every other aggregate.
"""

from __future__ import annotations

from typing import Protocol

from atlas.core.domain.knowledge_reference.entity import KnowledgeReference
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId


class KnowledgeReferenceRepository(Protocol):
    def add(self, knowledge_reference: KnowledgeReference) -> None:
        """Insert a new Knowledge Reference."""
        ...

    def get(self, knowledge_reference_id: KnowledgeReferenceId) -> KnowledgeReference | None:
        """Return a single Knowledge Reference by id, or None if it does not exist."""
        ...

    def list_all(self) -> list[KnowledgeReference]:
        """Return every Knowledge Reference ever captured, in chronological
        order: recorded_at ascending, then knowledge_reference_id as a
        deterministic final tie-breaker.
        """
        ...

    def delete(self, knowledge_reference_id: KnowledgeReferenceId) -> None:
        """Remove a Knowledge Reference by id. Idempotent: deleting an id
        that does not exist (already deleted, or never existed) is not an
        error at this layer — existence is the application service's
        concern (see `KnowledgeReferenceService.delete`), the same
        division of responsibility already used for `get`.
        """
        ...
