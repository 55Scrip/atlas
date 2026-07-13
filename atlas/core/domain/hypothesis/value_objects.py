"""Value objects for the Hypothesis aggregate (API-004 Hypothesis Capture)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.hypothesis.exceptions import MissingStatementError


@dataclass(frozen=True)
class HypothesisId:
    """Identity of a Hypothesis. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Statement:
    """The investor's provisional interpretation, explanation, or expectation.

    Not an Observation, not Evidence, not a Decision, not a truth claim.
    The API preserves the investor's own wording — no semantic validation
    of whether it "sounds like" a hypothesis is performed here or anywhere
    else in this aggregate.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingStatementError("Statement.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value
