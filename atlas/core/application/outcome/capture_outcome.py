"""Application service for the Outcome use case (ATLAS-001 Core Loop).

Verifies the referenced Decision exists (a pure read against
DecisionRepository) before constructing the new Outcome. Decision
(API-001) has no NotFoundError of its own, so this module defines one —
the same situation decision_context (API-002) was in. Never writes to
DecisionRepository.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.outcome.entity import Outcome
from atlas.core.domain.outcome.exceptions import DecisionNotFoundError, OutcomeNotFoundError
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.outcome.value_objects import OutcomeId, Statement


@dataclass(frozen=True)
class CaptureOutcomeRequest:
    decision_id: uuid.UUID
    statement: str
    occurred_at: datetime
    note: str | None = None


class OutcomeService:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        outcome_repository: OutcomeRepository,
    ) -> None:
        self._decisions = decision_repository
        self._outcomes = outcome_repository

    def capture(self, request: CaptureOutcomeRequest) -> Outcome:
        decision_id = DecisionId(request.decision_id)

        decision = self._decisions.get(decision_id)
        if decision is None:
            raise DecisionNotFoundError(f"No Decision found with id {decision_id}")

        outcome = Outcome.capture(
            case_id=decision.case_id,
            decision_id=decision_id,
            statement=Statement(request.statement),
            occurred_at=request.occurred_at,
            note=request.note,
        )
        self._outcomes.add(outcome)
        return outcome

    def get(self, outcome_id: OutcomeId) -> Outcome:
        outcome = self._outcomes.get(outcome_id)
        if outcome is None:
            raise OutcomeNotFoundError(f"No Outcome found with id {outcome_id}")
        return outcome

    def list_all(self) -> list[Outcome]:
        return self._outcomes.list_all()
