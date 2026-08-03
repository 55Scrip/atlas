"""Value objects for the Knowledge Reference aggregate (DO-IMP-003)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeReferenceId:
    """Identity of a Knowledge Reference. Generated once, at capture, and
    never reused.
    """

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)
