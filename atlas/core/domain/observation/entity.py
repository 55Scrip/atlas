"""The Observation aggregate root (API-003 Observation Capture).

Observation is something the investor noticed — not an interpretation, not
evidence, not a decision. It is immutable, and introduces no relationship
to Decision, DecisionContext, Hypothesis, or Evidence: this aggregate is
deliberately standalone. A note on naming: `atlas.domains.decision.models`
already defines an unrelated, differently-scoped `Observation` class
(evidence-derived, part of a reasoning pipeline) — a known legacy naming
collision, left untouched; see docs/ObservationCaptureAPI003.md.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.observation.exceptions import InvalidObservedAtError
from atlas.core.domain.observation.value_objects import ObservationId, Statement, Subject

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_observed_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidObservedAtError("Observation.observed_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidObservedAtError(
            f"Observation.observed_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidObservedAtError("Observation.observed_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Observation:
    """A single, immutable observation.

    Valid only if it carries an id, a subject, a statement, the moment it
    was observed, and the moment Atlas recorded it. Source and note are
    optional context: blank values normalize to None rather than being
    rejected or stored as empty strings.
    """

    id: ObservationId
    subject: Subject
    statement: Statement
    observed_at: datetime
    recorded_at: datetime
    source: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _validated_observed_at(self.observed_at))
        object.__setattr__(self, "source", _normalize_blank(self.source))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        subject: Subject,
        statement: Statement,
        observed_at: datetime,
        source: str | None = None,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Observation:
        """Capture a brand-new Observation.

        This is the only path that assigns identity and RecordedAt.
        ObservedAt is preserved exactly as given, offset and all — the
        same reasoning as `DecisionContext.captured_at`: it is the
        investor's own account of when they noticed something, not a
        value Atlas is free to renormalise. RecordedAt is always Atlas's
        own UTC clock.
        """
        now = clock()
        return cls(
            id=ObservationId(),
            subject=subject,
            statement=statement,
            observed_at=observed_at,
            recorded_at=now,
            source=source,
            note=note,
        )
