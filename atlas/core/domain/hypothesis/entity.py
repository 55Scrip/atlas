"""The Hypothesis aggregate root (API-004 Hypothesis Capture).

Hypothesis is the investor's provisional belief about what something may
mean — not an Observation, not Evidence, not a Decision, not an Outcome,
not a truth claim, and not an Atlas-generated conclusion. It is immutable,
and introduces no relationship to Observation, Decision, DecisionContext,
or Evidence: this aggregate is deliberately standalone, the same as
Observation (API-003).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.hypothesis.exceptions import InvalidFormulatedAtError
from atlas.core.domain.hypothesis.value_objects import HypothesisId, Statement

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_formulated_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidFormulatedAtError("Hypothesis.formulated_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidFormulatedAtError(
            f"Hypothesis.formulated_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidFormulatedAtError("Hypothesis.formulated_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Hypothesis:
    """A single, immutable provisional belief.

    Valid only if it carries an id, a statement, the moment it was
    formulated, and the moment Atlas recorded it. Note is optional
    context: blank values normalize to None rather than being rejected or
    stored as empty strings. Atlas assigns no truth value, confidence, or
    conviction to a Hypothesis — those are explicitly out of scope.
    """

    id: HypothesisId
    statement: Statement
    formulated_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "formulated_at", _validated_formulated_at(self.formulated_at))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        statement: Statement,
        formulated_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Hypothesis:
        """Capture a brand-new Hypothesis.

        This is the only path that assigns identity and RecordedAt.
        FormulatedAt is preserved exactly as given, offset and all — the
        same reasoning as `Observation.observed_at` and
        `DecisionContext.captured_at`: it is the investor's own account of
        when they formed the belief, not a value Atlas is free to
        renormalise. RecordedAt is always Atlas's own UTC clock. A changed
        belief is represented by capturing a new Hypothesis, never by
        mutating this one.
        """
        now = clock()
        return cls(
            id=HypothesisId(),
            statement=statement,
            formulated_at=formulated_at,
            recorded_at=now,
            note=note,
        )
