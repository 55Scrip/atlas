"""Value objects for the Evidence aggregate (API-005 Evidence Capture)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from atlas.core.domain.evidence.exceptions import InvalidDirectionError, MissingStatementError


@dataclass(frozen=True)
class EvidenceId:
    """Identity of an Evidence record. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Statement:
    """The information, fact, circumstance, or reasoning input the investor
    used as support or challenge.

    Not a truth claim: Atlas preserves that the investor regarded this as
    evidence, not that the information proves or disproves anything. No
    semantic validation of whether the text "sounds like" evidence is
    performed here or anywhere else in this aggregate.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingStatementError("Statement.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value


class Direction(str, Enum):
    """Whether the investor regarded this Evidence as supporting or
    challenging a line of reasoning.

    Deliberately limited to these two values. Evidence influences
    reasoning; it does not determine truth — there is no PROVES,
    DISPROVES, TRUE, FALSE, POSITIVE, NEGATIVE, CONFIRMING, or
    DISCONFIRMING here or anywhere else in this aggregate.
    """

    SUPPORTS = "SUPPORTS"
    CHALLENGES = "CHALLENGES"

    @classmethod
    def coerce(cls, value: Direction | str | None) -> Direction:
        if value is None:
            raise InvalidDirectionError("Direction must not be missing")
        if isinstance(value, Direction):
            return value
        try:
            return cls(value)
        except ValueError as exc:
            raise InvalidDirectionError(f"Unknown Direction: {value!r}") from exc
