"""Value objects for the Reasoning Trace aggregate (DO-IMP-009)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReasoningTraceId:
    """Identity of a Reasoning Trace. Generated once, at capture, and
    never reused.
    """

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)
