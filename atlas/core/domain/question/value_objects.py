"""Value objects for the Question aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.question.exceptions import MissingStatementError


@dataclass(frozen=True)
class QuestionId:
    """Identity of a Question. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Statement:
    """The question itself, in the investor's own words.

    The root of the Core Loop: "what am I trying to figure out?" No
    semantic validation of whether the text reads as a question is
    performed here or anywhere else in this aggregate.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingStatementError("Statement.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value
