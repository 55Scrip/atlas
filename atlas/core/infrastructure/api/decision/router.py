"""REST controller for Decision Capture (API-001).

POST /decisions        - register a new Decision
GET  /decisions        - list every recorded Decision
GET  /decisions/{id}   - read a single Decision
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from atlas.core.application.decision.capture_decision import (
    CaptureDecisionRequest,
    CaptureDecisionService,
)
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.api.decision.dependencies import (
    get_capture_decision_service,
    get_decision_repository,
)
from atlas.core.infrastructure.api.decision.schemas import (
    CreateDecisionRequest,
    DecisionCreatedResponse,
    DecisionSummary,
)

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("", response_model=DecisionCreatedResponse, status_code=201)
def create_decision(
    payload: CreateDecisionRequest,
    service: CaptureDecisionService = Depends(get_capture_decision_service),
) -> DecisionCreatedResponse:
    decision = service.capture(
        CaptureDecisionRequest(
            case_id=payload.case_id,
            user_id=payload.user_id,
            decision_type=payload.decision_type,
            reason=payload.reason,
            confidence=payload.confidence,
            decided_at=payload.decided_at,
            subject=payload.subject,
            source=payload.source,
            observation_id=payload.observation_id,
        )
    )
    return DecisionCreatedResponse.from_domain(decision)


@router.get("", response_model=list[DecisionSummary])
def list_decisions(
    repository: DecisionRepository = Depends(get_decision_repository),
) -> list[DecisionSummary]:
    return [DecisionSummary.from_domain(decision) for decision in repository.list_all()]


@router.get("/{decision_id}", response_model=DecisionSummary)
def get_decision(
    decision_id: uuid.UUID,
    repository: DecisionRepository = Depends(get_decision_repository),
) -> DecisionSummary:
    decision = repository.get(DecisionId(decision_id))
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return DecisionSummary.from_domain(decision)
