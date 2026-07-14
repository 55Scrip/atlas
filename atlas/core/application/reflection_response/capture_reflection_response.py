"""CaptureReflectionResponseService — the only path to a durable ReflectionResponse (ATLAS-009).

Called exactly once, only after Decision capture has already succeeded
(ATLAS-009-D §7) — this service does not verify that itself; the caller
(conversation/cli.py) is responsible for calling it only at that point.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from atlas.core.application.reflection_response.provisional_response import (
    ProvisionalReflectionResponse,
)
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.reflection_response.entity import ReflectionResponse
from atlas.core.domain.reflection_response.repository import ReflectionResponseRepository
from atlas.core.domain.reflection_response.value_objects import ResponseText

_Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CaptureReflectionResponseService:
    def __init__(self, repository: ReflectionResponseRepository) -> None:
        self._repository = repository

    def capture(
        self,
        provisional: ProvisionalReflectionResponse,
        *,
        decision_id: DecisionId,
        clock: _Clock = _utc_now,
    ) -> ReflectionResponse:
        response = ReflectionResponse.register(
            decision_id=decision_id,
            response_text=ResponseText(provisional.response_text),
            provenance=provisional.provenance,
            clock=clock,
        )
        self._repository.add(response)
        return response
