"""The Interpretation aggregate root (ATLAS-001 Core Loop).

Interpretation is the investor's reading of one specific, already-recorded
Observation: "why does this fact matter?" It is anchored — it mandatorily
carries the id of the Observation it interprets — which is what makes it
distinct from Hypothesis (a freestanding, unanchored belief that already
exists as its own aggregate and is left completely untouched by this
increment). Interpretation is immutable and references Observation only
by id, read-only; it never modifies Observation.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.interpretation.exceptions import InvalidInterpretedAtError
from atlas.core.domain.interpretation.value_objects import InterpretationId, Statement
from atlas.core.domain.observation.value_objects import ObservationId

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_interpreted_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidInterpretedAtError("Interpretation.interpreted_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidInterpretedAtError(
            f"Interpretation.interpreted_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidInterpretedAtError("Interpretation.interpreted_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Interpretation:
    """A single, immutable reading of one Observation.

    Valid only if it carries an id, the Observation it interprets, a
    statement, the moment it was interpreted, and the moment Atlas
    recorded it. Note is optional context: blank values normalize to
    None.
    """

    id: InterpretationId
    observation_id: ObservationId
    statement: Statement
    interpreted_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "interpreted_at", _validated_interpreted_at(self.interpreted_at)
        )
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        observation_id: ObservationId,
        statement: Statement,
        interpreted_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Interpretation:
        """Capture a brand-new Interpretation of an existing Observation.

        InterpretedAt is preserved exactly as given, offset and all.
        RecordedAt is always Atlas's own UTC clock. This classmethod does
        not verify the Observation exists — that existence check is an
        application-service concern, performed via a read-only lookup
        against ObservationRepository before this is called.
        """
        now = clock()
        return cls(
            id=InterpretationId(),
            observation_id=observation_id,
            statement=statement,
            interpreted_at=interpreted_at,
            recorded_at=now,
            note=note,
        )
