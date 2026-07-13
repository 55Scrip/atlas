"""Application service for the Decision Context use case (API-002).

This is where the two aggregates meet: it checks that the referenced
Decision exists and has no context yet, then constructs and persists a new
DecisionContext. It never writes to the Decision repository — only reads
from it — so capturing context cannot modify the referenced Decision.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.domain.decision_context.exceptions import (
    DecisionNotFoundError,
    DuplicateDecisionContextError,
)
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.domain.decision_context.value_objects import (
    AlternativesConsidered,
    Situation,
    Uncertainties,
)


@dataclass(frozen=True)
class CaptureDecisionContextRequest:
    decision_id: uuid.UUID
    situation: str
    captured_at: datetime
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()


class CaptureDecisionContextService:
    def __init__(
        self,
        decision_repository: DecisionRepository,
        decision_context_repository: DecisionContextRepository,
    ) -> None:
        self._decisions = decision_repository
        self._contexts = decision_context_repository

    def capture(self, request: CaptureDecisionContextRequest) -> DecisionContext:
        decision_id = DecisionId(request.decision_id)

        if self._decisions.get(decision_id) is None:
            raise DecisionNotFoundError(f"No Decision found with id {decision_id}")

        if self._contexts.get_by_decision_id(decision_id) is not None:
            raise DuplicateDecisionContextError(
                f"DecisionContext already exists for Decision {decision_id}"
            )

        context = DecisionContext.capture(
            decision_id=decision_id,
            situation=Situation(request.situation),
            captured_at=request.captured_at,
            portfolio_relevance=request.portfolio_relevance,
            capital_considerations=request.capital_considerations,
            alternatives_considered=AlternativesConsidered(tuple(request.alternatives_considered)),
            uncertainties=Uncertainties(tuple(request.uncertainties)),
        )
        self._contexts.add(context)
        return context
