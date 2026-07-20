"""Repository interface for the Case aggregate.

Insert-only: no update, no delete, matching every other aggregate in
this codebase. No `list_all`: nothing within DO-IMP-001's approved scope
needs to enumerate every Case yet — adding it now would be adding an
operation beyond what the current use case requires.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.case.entity import Case
from atlas.core.domain.case.value_objects import CaseId


class CaseRepository(Protocol):
    def add(self, case: Case) -> None:
        """Insert a new Case."""
        ...

    def get(self, case_id: CaseId) -> Case | None:
        """Return a single Case by id, or None if it does not exist."""
        ...
