"""Repository interface for the Judgment aggregate.

Insert-only: no update, no delete, matching every other aggregate in
this codebase. No `list_all`: nothing within DO-IMP-004's approved
scope needs to enumerate every Judgment yet.
"""
from __future__ import annotations

from typing import Protocol

from atlas.core.domain.judgment.entity import Judgment
from atlas.core.domain.judgment.value_objects import JudgmentId


class JudgmentRepository(Protocol):
    def add(self, judgment: Judgment) -> None:
        """Insert a new Judgment."""
        ...

    def get(self, judgment_id: JudgmentId) -> Judgment | None:
        """Return a single Judgment by id, or None if it does not exist."""
        ...
