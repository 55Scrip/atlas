"""Value objects for the Case aggregate (DO-IMP-001 Case Aggregate)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CaseId:
    """Identity of a Case. Generated once, at creation, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)
