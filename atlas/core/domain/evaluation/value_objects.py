"""Value objects for the Evaluation aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from atlas.core.domain.evaluation.exceptions import MissingStatementError


@dataclass(frozen=True)
class EvaluationId:
    """Identity of an Evaluation. Generated once, at capture, and never reused."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Statement:
    """The investor's assessment of an Outcome against what was expected.

    No semantic validation of the text is performed here or anywhere
    else in this aggregate.
    """

    value: str

    def __post_init__(self) -> None:
        if self.value is None or not self.value.strip():
            raise MissingStatementError("Statement.value must not be empty")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value
