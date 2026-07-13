"""REST controller for Decision Context (API-002).

POST /decisions/{decision_id}/context - attach context to an existing Decision
GET  /decisions/{decision_id}/context - read the context for a Decision

No list, update, patch, or delete endpoints — a Decision has at most one
DecisionContext, and it is never replaced once captured.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from atlas.core.application.decision_context.capture_decision_context import (
    CaptureDecisionContextRequest,
    CaptureDecisionContextService,
)
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.domain.decision_context.repository import DecisionContextRepository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_repository
from atlas.core.infrastructure.api.decision_context.dependencies import (
    get_capture_decision_context_service,
    get_decision_context_repository,
)
from atlas.core.infrastructure.api.decision_context.schemas import (
    CreateDecisionContextRequest,
    DecisionContextResponse,
)

router = APIRouter(prefix="/decisions", tags=["decision-context"])


@router.post(
    "/{decision_id}/context", response_model=DecisionContextResponse, status_code=201
)
def create_decision_context(
    decision_id: uuid.UUID,
    payload: CreateDecisionContextRequest,
    service: CaptureDecisionContextService = Depends(get_capture_decision_context_service),
) -> DecisionContextResponse:
    context = service.capture(
        CaptureDecisionContextRequest(
            decision_id=decision_id,
            situation=payload.situation,
            captured_at=payload.captured_at,
            portfolio_relevance=payload.portfolio_relevance,
            capital_considerations=payload.capital_considerations,
            alternatives_considered=tuple(payload.alternatives_considered),
            uncertainties=tuple(payload.uncertainties),
        )
    )
    return DecisionContextResponse.from_domain(context)


@router.get("/{decision_id}/context", response_model=DecisionContextResponse)
def get_decision_context(
    decision_id: uuid.UUID,
    decision_repository: DecisionRepository = Depends(get_decision_repository),
    context_repository: DecisionContextRepository = Depends(get_decision_context_repository),
) -> DecisionContextResponse:
    if decision_repository.get(DecisionId(decision_id)) is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    context = context_repository.get_by_decision_id(DecisionId(decision_id))
    if context is None:
        raise HTTPException(status_code=404, detail="No context recorded for this Decision")

    return DecisionContextResponse.from_domain(context)
