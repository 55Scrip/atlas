"""Repository interface for the Knowledge Reference aggregate.

Insert-only: no update, no delete, matching every other aggregate in
this codebase. No `list_all`: nothing within DO-IMP-003's approved
scope needs to enumerate every Knowledge Reference yet.
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
