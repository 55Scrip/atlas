"""The Decision aggregate root (API-001 Decision Capture).

Decision is the smallest meaningful learning unit in Atlas: a single
investment decision, preserved exactly as it was reasoned at the time it was
made. There is no update. A changed opinion is a new Decision.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.exceptions import InvalidDecidedAtError
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionId,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_decided_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidDecidedAtError("Decision.decided_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidDecidedAtError(
            f"Decision.decided_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidDecidedAtError("Decision.decided_at must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Decision:
    """A single, immutable investment decision.

    Valid only if it carries an id, a decision type, a subject, an
    investment case, a confidence level, and the moment it was decided.
    Source is the only field that is context rather than invariant.
    """

    id: DecisionId
    case_id: CaseId
    user_id: UserId
    decision_type: DecisionType
    subject: Subject
    investment_case: InvestmentCase
    confidence: Confidence
    decided_at: datetime
    recorded_at: datetime
    source: DecisionSource = DecisionSource.MANUAL

    def __post_init__(self) -> None:
        object.__setattr__(self, "decided_at", _validated_decided_at(self.decided_at))

    @classmethod
    def register(
        cls,
        *,
        case_id: CaseId,
        user_id: UserId,
        decision_type: DecisionType | str,
        subject: Subject,
        investment_case: InvestmentCase,
        confidence: Confidence,
        decided_at: datetime | None = None,
        source: DecisionSource = DecisionSource.MANUAL,
        clock: _Clock = _utc_now,
    ) -> Decision:
        """Capture a brand-new Decision.

        This is the only path that assigns identity and RecordedAt: identity
        is always fresh, and RecordedAt is always "now" from Atlas's point of
        view, regardless of when the investor says the decision happened.
        """
        now = clock()
        return cls(
            id=DecisionId(),
            case_id=case_id,
            user_id=user_id,
            decision_type=DecisionType.coerce(decision_type),
            subject=subject,
            investment_case=investment_case,
            confidence=confidence,
            decided_at=decided_at if decided_at is not None else now,
            recorded_at=now,
            source=source,
        )
