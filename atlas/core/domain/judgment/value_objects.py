"""Value objects for the Judgment aggregate (DO-IMP-004)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.judgment.exceptions import MissingCharacterizationError


@dataclass(frozen=True)
class JudgmentId:
    """Identity of a Judgment. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Characterization:
    """The Case's settled characterization of its Judgment's subject.

    Canonically forced content (OE-002 §5.4; Judgment-Implementation-Design.md
    Section 11): a Judgment with no characterization would be structurally
    indistinguishable from a Knowledge Reference. Required in both the
    internal-content and referential forms — it is the one field every
    Judgment always carries.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingCharacterizationError("Characterization.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value
