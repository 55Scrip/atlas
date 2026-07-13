"""Value objects for the DecisionContext aggregate (API-002 Decision Context)."""
from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field

from atlas.core.domain.decision_context.exceptions import (
    InvalidAlternativeError,
    InvalidUncertaintyError,
    MissingSituationError,
)


@dataclass(frozen=True)
class ContextId:
    """Identity of a DecisionContext. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Situation:
    """The relevant circumstances the investor believed mattered at decision time."""

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingSituationError("Situation.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())


def _validated_items(
    values: tuple[str, ...], error_cls: type[Exception], label: str
) -> tuple[str, ...]:
    validated = []
    for item in values:
        if item is None or not item.strip():
            raise error_cls(f"{label} must not contain an empty value")
        validated.append(item.strip())
    return tuple(validated)


@dataclass(frozen=True)
class AlternativesConsidered:
    """The other options the investor weighed, in the order considered. May be empty."""

    items: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "items",
            _validated_items(tuple(self.items), InvalidAlternativeError, "AlternativesConsidered"),
        )

    def __iter__(self) -> Iterator[str]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)


@dataclass(frozen=True)
class Uncertainties:
    """What the investor was unsure about at decision time, in the order raised. May be empty."""

    items: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "items",
            _validated_items(tuple(self.items), InvalidUncertaintyError, "Uncertainties"),
        )

    def __iter__(self) -> Iterator[str]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
