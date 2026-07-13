"""The Learning aggregate root (ATLAS-001 Core Loop).

Learning is the distilled lesson drawn from one Evaluation — the
terminal node of the Core Loop: Question -> Observation ->
Interpretation -> Hypothesis -> Evidence -> Conclusion -> Decision ->
Outcome -> Evaluation -> Learning. It is immutable and references
Evaluation only by id, read-only; it never modifies Evaluation.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.evaluation.value_objects import EvaluationId
from atlas.core.domain.learning.exceptions import InvalidLearnedAtError
from atlas.core.domain.learning.value_objects import LearningId, Statement

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_learned_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidLearnedAtError("Learning.learned_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidLearnedAtError(
            f"Learning.learned_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidLearnedAtError("Learning.learned_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Learning:
    """A single, immutable lesson drawn from one Evaluation.

    Valid only if it carries an id, the Evaluation it draws from, a
    statement, the moment it was learned, and the moment Atlas recorded
    it. Note is optional context: blank values normalize to None.
    """

    id: LearningId
    evaluation_id: EvaluationId
    statement: Statement
    learned_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "learned_at", _validated_learned_at(self.learned_at))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        evaluation_id: EvaluationId,
        statement: Statement,
        learned_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Learning:
        """Capture a brand-new Learning from an existing Evaluation.

        LearnedAt is preserved exactly as given, offset and all.
        RecordedAt is always Atlas's own UTC clock. This classmethod does
        not verify the Evaluation exists — that existence check is an
        application-service concern, performed via a read-only lookup
        against EvaluationRepository before this is called.
        """
        now = clock()
        return cls(
            id=LearningId(),
            evaluation_id=evaluation_id,
            statement=statement,
            learned_at=learned_at,
            recorded_at=now,
            note=note,
        )
