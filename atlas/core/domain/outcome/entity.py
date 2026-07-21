"""The Outcome aggregate root (ATLAS-001 Core Loop).

Outcome is what actually happened after a Decision. It is immutable and
references Decision only by id, read-only; it never modifies Decision.
A Decision may accrue more than one Outcome entry over time (e.g. an
interim reading followed by a final one) — there is no uniqueness
constraint on decision_id.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.exceptions import InvalidOccurredAtError
from atlas.core.domain.outcome.value_objects import OutcomeId, Statement

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_occurred_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidOccurredAtError("Outcome.occurred_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidOccurredAtError(
            f"Outcome.occurred_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidOccurredAtError("Outcome.occurred_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Outcome:
    """A single, immutable record of what happened after a Decision.

    Valid only if it carries an id, the Decision it followed from, a
    statement, the moment it occurred, and the moment Atlas recorded it.
    Note is optional context: blank values normalize to None.
    """

    id: OutcomeId
    case_id: CaseId
    decision_id: DecisionId
    statement: Statement
    occurred_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "occurred_at", _validated_occurred_at(self.occurred_at))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        case_id: CaseId,
        decision_id: DecisionId,
        statement: Statement,
        occurred_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Outcome:
        """Capture a brand-new Outcome of an existing Decision.

        OccurredAt is preserved exactly as given, offset and all.
        RecordedAt is always Atlas's own UTC clock. This classmethod does
        not verify the Decision exists — that existence check is an
        application-service concern, performed via a read-only lookup
        against DecisionRepository before this is called.
        """
        now = clock()
        return cls(
            id=OutcomeId(),
            case_id=case_id,
            decision_id=decision_id,
            statement=statement,
            occurred_at=occurred_at,
            recorded_at=now,
            note=note,
        )
