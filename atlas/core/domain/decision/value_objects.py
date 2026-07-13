"""Value objects for the Decision aggregate (API-001 Decision Capture)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from atlas.core.domain.decision.exceptions import (
    InvalidConfidenceError,
    InvalidDecisionTypeError,
    MissingDecisionTypeError,
    MissingReasonError,
    MissingSubjectError,
)


@dataclass(frozen=True)
class DecisionId:
    """Identity of a Decision. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class UserId:
    """Identity of the investor who owns a Decision."""

    value: uuid.UUID

    def __str__(self) -> str:
        return str(self.value)


class DecisionType(str, Enum):
    """The action the investor decided to take."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"
    PASS = "PASS"

    @classmethod
    def coerce(cls, value: DecisionType | str | None) -> DecisionType:
        if value is None:
            raise MissingDecisionTypeError("DecisionType must not be missing")
        if isinstance(value, DecisionType):
            return value
        try:
            return cls(value)
        except ValueError as exc:
            raise InvalidDecisionTypeError(f"Unknown DecisionType: {value!r}") from exc


class DecisionSource(str, Enum):
    """Where a Decision entered Atlas from."""

    MANUAL = "Manual"
    IMPORT = "Import"
    BROKER_SYNC = "BrokerSync"
    API = "API"


@dataclass(frozen=True)
class Subject:
    """What the decision is about — e.g. a ticker or company name.

    Every investment decision is a decision about something. Subject is
    therefore a required aggregate invariant, not optional context.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingSubjectError("Subject.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class InvestmentCase:
    """The original reasoning that existed when the decision was made.

    Not a later reflection: this is captured once, at decision time, and never
    edited to match hindsight.
    """

    reason: str

    def __post_init__(self) -> None:
        if self.reason is None or not self.reason.strip():
            raise MissingReasonError("InvestmentCase.reason must not be empty")
        object.__setattr__(self, "reason", self.reason.strip())


@dataclass(frozen=True)
class Confidence:
    """The investor's own conviction level at decision time, 0-100.

    Atlas stores this. It does not interpret it.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvalidConfidenceError(
                f"Confidence must be an integer, got {type(self.value).__name__}"
            )
        if not (0 <= self.value <= 100):
            raise InvalidConfidenceError(
                f"Confidence must be between 0 and 100, got {self.value}"
            )
