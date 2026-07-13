"""The Evidence aggregate root (API-005 Evidence Capture).

Evidence is a time-bound record of information the investor considered
supportive of or challenging to a line of reasoning. It does not represent
objective truth: Atlas preserves that the investor regarded this
information as evidence, not that the information proves or disproves
anything. It is immutable, and introduces no relationship to Hypothesis,
Observation, Decision, or DecisionContext: this aggregate is deliberately
standalone, the same as Observation (API-003) and Hypothesis (API-004).

A note on naming: `atlas.domains.decision.models.Evidence` and the
`atlas.evidence` package already use the word "Evidence" for an unrelated,
automated evidence-quality-assessment concept (strength grading,
confidence impact, source credibility) — a known legacy naming collision,
left untouched; see docs/EvidenceCaptureAPI005.md.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.evidence.exceptions import InvalidObservedAtError
from atlas.core.domain.evidence.value_objects import Direction, EvidenceId, Statement

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_observed_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidObservedAtError("Evidence.observed_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidObservedAtError(
            f"Evidence.observed_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidObservedAtError("Evidence.observed_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Evidence:
    """A single, immutable record of investor-assessed evidence.

    Valid only if it carries an id, a statement, a direction (SUPPORTS or
    CHALLENGES), the moment the information was observed, and the moment
    Atlas recorded it. Source and note are optional context: blank values
    normalize to None rather than being rejected or stored as empty
    strings. A correction is represented by capturing a new Evidence
    record, never by mutating this one.
    """

    id: EvidenceId
    statement: Statement
    direction: Direction
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
        statement: Statement,
        direction: Direction | str,
        observed_at: datetime,
        source: str | None = None,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Evidence:
        """Capture a brand-new Evidence record.

        This is the only path that assigns identity and RecordedAt.
        ObservedAt is preserved exactly as given, offset and all — the
        same reasoning as `Observation.observed_at` and
        `Hypothesis.formulated_at`: it is the investor's own account of
        when the information became known or relevant, not a value Atlas
        is free to renormalise. RecordedAt is always Atlas's own UTC
        clock.
        """
        now = clock()
        return cls(
            id=EvidenceId(),
            statement=statement,
            direction=Direction.coerce(direction),
            observed_at=observed_at,
            recorded_at=now,
            source=source,
            note=note,
        )
