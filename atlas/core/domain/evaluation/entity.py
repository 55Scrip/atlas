"""The Evaluation aggregate root (ATLAS-001 Core Loop).

Evaluation is the investor's assessment of an Outcome: did it confirm or
contradict what was expected, and why? It is immutable and references
Outcome only by id, read-only; it never modifies Outcome.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.evaluation.exceptions import InvalidEvaluatedAtError
from atlas.core.domain.evaluation.value_objects import EvaluationId, Statement
from atlas.core.domain.outcome.value_objects import OutcomeId

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_evaluated_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidEvaluatedAtError("Evaluation.evaluated_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidEvaluatedAtError(
            f"Evaluation.evaluated_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidEvaluatedAtError("Evaluation.evaluated_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Evaluation:
    """A single, immutable assessment of one Outcome.

    Valid only if it carries an id, the Outcome it evaluates, a
    statement, the moment it was evaluated, and the moment Atlas
    recorded it. Note is optional context: blank values normalize to
    None.
    """

    id: EvaluationId
    outcome_id: OutcomeId
    statement: Statement
    evaluated_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evaluated_at", _validated_evaluated_at(self.evaluated_at))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        outcome_id: OutcomeId,
        statement: Statement,
        evaluated_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Evaluation:
        """Capture a brand-new Evaluation of an existing Outcome.

        EvaluatedAt is preserved exactly as given, offset and all.
        RecordedAt is always Atlas's own UTC clock. This classmethod does
        not verify the Outcome exists — that existence check is an
        application-service concern, performed via a read-only lookup
        against OutcomeRepository before this is called.
        """
        now = clock()
        return cls(
            id=EvaluationId(),
            outcome_id=outcome_id,
            statement=statement,
            evaluated_at=evaluated_at,
            recorded_at=now,
            note=note,
        )
