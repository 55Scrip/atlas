"""Value objects for the Observation aggregate (API-003 Observation Capture)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.observation.exceptions import (
    MissingStatementError,
    MissingSubjectError,
)


@dataclass(frozen=True)
class ObservationId:
    """Identity of an Observation. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Subject:
    """What the observation concerns — a company, sector, market, or the
    investor's own portfolio.

    Deliberately its own value object, not a reuse of
    `atlas.core.domain.decision.value_objects.Subject`: API-003 introduces
    no relationship to Decision, and this Subject is broader in practice
    (e.g. "US interest rates", "My portfolio liquidity" — not necessarily
    a ticker).
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingSubjectError("Subject.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Statement:
    """A factual description of what the investor observed.

    Not an interpretation, not evidence, not a decision — just the thing
    that was noticed.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingStatementError("Statement.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value
