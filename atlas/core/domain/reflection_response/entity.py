"""The ReflectionResponse aggregate root (ATLAS-009).

ReflectionResponse is occasion-originated but durably preserved
(ATLAS-009-D §2) — the first concept in the Understanding lineage
(Decision Timeline, Pattern, Strategy Signature, Decision Reflection,
Decision Coach) whose purpose is to persist rather than remain
ephemeral. It is authored only by the investor: Atlas contributes no
content to it, only the provenance snapshot of what the investor saw.

decision_id is the only durable-identity reference this aggregate
holds — valid because a Decision, once recorded, never changes. Every
other field is a snapshot of plain values, never a reference to an
ephemeral object (ATLAS-009-D §4).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.value_objects import (
    ProvenanceSnapshot,
    ReflectionResponseId,
    ResponseText,
)

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ReflectionResponse:
    """A single, immutable record of an investor's own preserved words.

    Valid only if it carries an id, the Decision it is anchored to, the
    investor's own response text, the provenance snapshot of what
    prompted it, and the moment Atlas recorded it.
    """

    id: ReflectionResponseId
    decision_id: DecisionId
    response_text: ResponseText
    provenance: ProvenanceSnapshot
    recorded_at: datetime

    @classmethod
    def register(
        cls,
        *,
        decision_id: DecisionId,
        response_text: ResponseText,
        provenance: ProvenanceSnapshot,
        clock: _Clock = _utc_now,
    ) -> ReflectionResponse:
        """Capture a brand-new ReflectionResponse, anchored to an
        already-recorded Decision.

        This classmethod does not verify the Decision exists — the
        caller is responsible for calling this only once Decision
        capture has already succeeded (ATLAS-009-D §7).
        """
        return cls(
            id=ReflectionResponseId(),
            decision_id=decision_id,
            response_text=response_text,
            provenance=provenance,
            recorded_at=clock(),
        )
