"""The Conclusion aggregate root (ATLAS-001 Core Loop).

Conclusion is the output of the reasoning process: what the investor
concludes after weighing Evidence. Conceptually broader than "a
conclusion from one piece of evidence" — for ATLAS-001, it is anchored
to a single Evidence record (`evidence_id`) as an explicit, documented
implementation simplification matching this sprint's "one complete
reasoning cycle" scope (see docs/CoreLoopATLAS001.md). A future
increment extending this to multiple Evidence records plus a direct
Hypothesis reference is expected, not merely possible. Conclusion is
immutable and references Evidence only by id, read-only; it never
modifies Evidence.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.conclusion.exceptions import InvalidConcludedAtError
from atlas.core.domain.conclusion.value_objects import ConclusionId, Statement
from atlas.core.domain.evidence.value_objects import EvidenceId

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validated_concluded_at(value: datetime | None) -> datetime:
    if value is None:
        raise InvalidConcludedAtError("Conclusion.concluded_at must not be missing")
    if not isinstance(value, datetime):
        raise InvalidConcludedAtError(
            f"Conclusion.concluded_at must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None:
        raise InvalidConcludedAtError("Conclusion.concluded_at must be timezone-aware")
    return value


def _normalize_blank(value: str | None) -> str | None:
    """Blank optional text normalizes to None; meaningful text is stripped."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass(frozen=True)
class Conclusion:
    """A single, immutable conclusion drawn from one Evidence record.

    Valid only if it carries an id, the Evidence it concludes from, a
    statement, the moment it was concluded, and the moment Atlas
    recorded it. Note is optional context: blank values normalize to
    None.
    """

    id: ConclusionId
    evidence_id: EvidenceId
    statement: Statement
    concluded_at: datetime
    recorded_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concluded_at", _validated_concluded_at(self.concluded_at))
        object.__setattr__(self, "note", _normalize_blank(self.note))

    @classmethod
    def capture(
        cls,
        *,
        evidence_id: EvidenceId,
        statement: Statement,
        concluded_at: datetime,
        note: str | None = None,
        clock: _Clock = _utc_now,
    ) -> Conclusion:
        """Draw a brand-new Conclusion from an existing Evidence record.

        ConcludedAt is preserved exactly as given, offset and all.
        RecordedAt is always Atlas's own UTC clock. This classmethod does
        not verify the Evidence exists — that existence check is an
        application-service concern, performed via a read-only lookup
        against EvidenceRepository before this is called.
        """
        now = clock()
        return cls(
            id=ConclusionId(),
            evidence_id=evidence_id,
            statement=statement,
            concluded_at=concluded_at,
            recorded_at=now,
            note=note,
        )
