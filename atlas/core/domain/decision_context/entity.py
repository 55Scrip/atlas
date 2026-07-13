"""The DecisionContext aggregate root (API-002 Decision Context).

DecisionContext is a point-in-time record of the circumstances surrounding
an existing Decision — not a live view of the current portfolio, not market
data, not a later reflection. It is a separate aggregate from Decision
(API-001): Decision remains stable and minimal, context may be captured
later, and neither aggregate can rewrite the other's history.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.exceptions import InvalidCapturedAtError
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    ContextId,
    Situation,
    Uncertainties,
)

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_captured_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidCapturedAtError("DecisionContext.captured_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidCapturedAtError(
            f"DecisionContext.captured_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidCapturedAtError("DecisionContext.captured_at must be timezone-aware")
    return value


@dataclass(frozen=True)
class DecisionContext:
    """The circumstances surrounding a Decision, as they were at the time.

    Valid only if it carries an id, a reference to an existing Decision, a
    situation, the moment those circumstances applied, and the moment Atlas
    recorded them. Everything else is optional detail.
    """

    context_id: ContextId
    decision_id: DecisionId
    situation: Situation
    captured_at: datetime
    recorded_at: datetime
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: AlternativesConsidered = field(default_factory=AlternativesConsidered)
    uncertainties: Uncertainties = field(default_factory=Uncertainties)

    def __post_init__(self) -> None:
        object.__setattr__(self, "captured_at", _validated_captured_at(self.captured_at))

    @classmethod
    def capture(
        cls,
        *,
        decision_id: DecisionId,
        situation: Situation,
        captured_at: datetime,
        portfolio_relevance: str | None = None,
        capital_considerations: str | None = None,
        alternatives_considered: AlternativesConsidered | None = None,
        uncertainties: Uncertainties | None = None,
        clock: _Clock = _utc_now,
    ) -> DecisionContext:
        """Capture the circumstances surrounding an existing Decision.

        This is the only path that assigns identity and RecordedAt.
        CapturedAt is preserved exactly as given, offset and all — it is the
        investor's own account of when those circumstances applied, and
        Atlas is not free to renormalise it the way Decision.decided_at
        renormalises to UTC.
        """
        return cls(
            context_id=ContextId(),
            decision_id=decision_id,
            situation=situation,
            captured_at=captured_at,
            recorded_at=clock(),
            portfolio_relevance=portfolio_relevance,
            capital_considerations=capital_considerations,
            alternatives_considered=alternatives_considered or AlternativesConsidered(),
            uncertainties=uncertainties or Uncertainties(),
        )
