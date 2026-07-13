"""HTTP request/response schemas for Decision Context (API-002).

Per the API-002 specification's own example, this endpoint's JSON uses
camelCase (`portfolioRelevance`, `capturedAt`, ...) — unlike API-001's
snake_case. That is a real inconsistency across the two endpoints, kept
here deliberately because the spec's example is explicit about it; see
docs/DecisionContextAPI002.md for the observation.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from atlas.core.domain.decision_context.entity import DecisionContext


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CreateDecisionContextRequest(_CamelModel):
    situation: str
    captured_at: datetime
    portfolio_relevance: str | None = None
    capital_considerations: str | None = None
    alternatives_considered: list[str] = []
    uncertainties: list[str] = []


class DecisionContextResponse(_CamelModel):
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
