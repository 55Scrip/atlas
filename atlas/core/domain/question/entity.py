"""The Question aggregate root (ATLAS-001 Core Loop).

Question is the root of the Core Loop: Question -> Observation ->
Interpretation -> Hypothesis -> Evidence -> Conclusion -> Decision ->
Outcome -> Evaluation -> Learning. It is immutable and references no
other aggregate — it is the one node in the cycle with nothing upstream
of it.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.question.exceptions import InvalidRaisedAtError
from atlas.core.domain.question.value_objects import QuestionId, Statement

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_raised_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidRaisedAtError("Question.raised_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidRaisedAtError(
            f"Question.raised_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidRaisedAtError("Question.raised_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Question:
    """A single, immutable question the investor is trying to answer.

    Valid only if it carries an id, a statement, the moment it was
    raised, and the moment Atlas recorded it. Note is optional context:
    blank values normalize to None.
    """

    id: QuestionId
    statement: Statement
    raised_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "raised_at", _validated_raised_at(self.raised_at))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        statement: Statement,
        raised_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Question:
        """Raise a brand-new Question.

        RaisedAt is preserved exactly as given, offset and all — the
        same reasoning as every other investor-supplied timestamp in
        this domain. RecordedAt is always Atlas's own UTC clock.
        """
        now = clock()
        return cls(
            id=QuestionId(),
            statement=statement,
            raised_at=raised_at,
            recorded_at=now,
            note=note,
        )
