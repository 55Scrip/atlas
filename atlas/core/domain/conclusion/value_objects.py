"""Value objects for the Conclusion aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.conclusion.exceptions import MissingStatementError


@dataclass(frozen=True)
class ConclusionId:
    """Identity of a Conclusion. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Statement:
    """The output of the reasoning process, as the investor states it.

    For ATLAS-001, a Conclusion is anchored to a single Evidence record
    (see entity.py docstring) as an explicit implementation
    simplification for this sprint's "one complete reasoning cycle"
    scope — conceptually, a Conclusion represents the reasoning process's
    output, not merely "a conclusion from one piece of evidence." No
    semantic validation of the text is performed here or anywhere else
    in this aggregate.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingStatementError("Statement.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value
