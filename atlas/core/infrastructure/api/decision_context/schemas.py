"""HTTP request/response schemas for Decision Context (API-002).

Per ADR-004, all public REST API schemas share one camelCase wire format
via `CamelModel` (`atlas.core.infrastructure.api.serialization`). API-002
was the first endpoint to use camelCase, ahead of the standard being
formalized — it originally defined its own local `_CamelModel`; this now
points at the shared one instead, with no behavior change.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from atlas.core.domain.decision_context.entity import DecisionContext
from atlas.core.infrastructure.api.serialization import CamelModel


class CreateDecisionContextRequest(CamelModel):
    situation: str
    captured_at: datetime
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: list[str] = []
    uncertainties: list[str] = []


class DecisionContextResponse(CamelModel):
    context_id: uuid.UUID
    decision_id: uuid.UUID
    situation: str
    portfolio_relevance: str | None
    capital_considerations: str | None
    alternatives_considered: list[str]
    uncertainties: list[str]
    captured_at: datetime
    recorded_at: datetime

    @classmethod
    def from_domain(cls, context: DecisionContext) -> DecisionContextResponse:
        return cls(
            context_id=context.context_id.value,
            decision_id=context.decision_id.value,
            situation=context.situation.value,
            portfolio_relevance=context.portfolio_relevance,
            capital_considerations=context.capital_considerations,
            alternatives_considered=list(context.alternatives_considered),
            uncertainties=list(context.uncertainties),
            captured_at=context.captured_at,
            recorded_at=context.recorded_at,
        )
