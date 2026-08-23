"""REST controller for CaseCondition (ADR-CC-001).

POST   /cases/{case_id}/case-conditions               - create a new condition
GET    /cases/{case_id}/case-conditions               - list conditions for a Case
GET    /decisions/{decision_id}/case-conditions        - list conditions for a Decision
GET    /case-conditions/{condition_id}                 - read one condition's current state
GET    /case-conditions/{condition_id}/events           - full event history
PATCH  /case-conditions/{condition_id}                 - revise a condition's content
POST   /case-conditions/{condition_id}/evaluate         - mechanically evaluate or record a human assertion
POST   /case-conditions/{condition_id}/retire           - retire (idempotent, terminal)
POST   /case-conditions/{condition_id}/supersede        - supersede (terminal)

Routes and conventions mirror `decision_draft/router.py` (Sprint 9)
directly: case-scoped creation/listing, condition-scoped everything
else, `Query(alias=...)` for camelCase query parameters (ADR-004).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response

from atlas.core.application.case_condition.case_condition_service import (
    CaseConditionContent,
    CaseConditionService,
)
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.api.case_condition.dependencies import get_case_condition_service
from atlas.core.infrastructure.api.case_condition.schemas import (
    CaseConditionEvaluationResponse,
    CaseConditionResponse,
    CreateCaseConditionRequest,
    EvaluateCaseConditionRequest,
    ReviseCaseConditionRequest,
    SupersedeCaseConditionRequest,
)

router = APIRouter(tags=["case-conditions"])


def _content_from_create(payload: CreateCaseConditionRequest) -> CaseConditionContent:
    return CaseConditionContent(
        predicate_text=payload.predicate_text,
        role=payload.role,
        authorship=payload.authorship,
        structured_kind=payload.structured_kind,
        threshold_date=payload.threshold_date,
        threshold_metric=payload.threshold_metric,
        threshold_operator=payload.threshold_operator,
        threshold_value=payload.threshold_value,
    )


def _content_from_revise(payload: ReviseCaseConditionRequest) -> CaseConditionContent:
    return CaseConditionContent(
        predicate_text=payload.predicate_text,
        role=payload.role,
        authorship=payload.authorship,
        structured_kind=payload.structured_kind,
        threshold_date=payload.threshold_date,
        threshold_metric=payload.threshold_metric,
        threshold_operator=payload.threshold_operator,
        threshold_value=payload.threshold_value,
    )


@router.post(
    "/cases/{case_id}/case-conditions", response_model=CaseConditionResponse, status_code=201
)
def create_case_condition(
    case_id: uuid.UUID,
    payload: CreateCaseConditionRequest,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> CaseConditionResponse:
    view = service.create(
        case_id=CaseId(case_id),
        decision_id=DecisionId(payload.decision_id) if payload.decision_id is not None else None,
        content=_content_from_create(payload),
    )
    return CaseConditionResponse.from_domain(view)


@router.get("/cases/{case_id}/case-conditions", response_model=list[CaseConditionResponse])
def list_case_conditions_for_case(
    case_id: uuid.UUID,
    include_terminal: bool = Query(default=False, alias="includeTerminal"),
    service: CaseConditionService = Depends(get_case_condition_service),
) -> list[CaseConditionResponse]:
    views = service.list_for_case(CaseId(case_id), include_terminal=include_terminal)
    return [CaseConditionResponse.from_domain(view) for view in views]


@router.get(
    "/decisions/{decision_id}/case-conditions", response_model=list[CaseConditionResponse]
)
def list_case_conditions_for_decision(
    decision_id: uuid.UUID,
    include_terminal: bool = Query(default=False, alias="includeTerminal"),
    service: CaseConditionService = Depends(get_case_condition_service),
) -> list[CaseConditionResponse]:
    views = service.list_for_decision(DecisionId(decision_id), include_terminal=include_terminal)
    return [CaseConditionResponse.from_domain(view) for view in views]


@router.get("/case-conditions/{condition_id}", response_model=CaseConditionResponse)
def get_case_condition(
    condition_id: uuid.UUID,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> CaseConditionResponse:
    view = service.read(CaseConditionId(condition_id))
    return CaseConditionResponse.from_domain(view)


@router.get("/case-conditions/{condition_id}/events")
def list_case_condition_events(
    condition_id: uuid.UUID,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> list[dict]:
    events = service.list_events(CaseConditionId(condition_id))
    return [
        {
            "id": event.id,
            "eventType": event.event_type,
            "recordedAt": event.recorded_at.isoformat(),
            "observedValue": event.observed_value,
            "supersededByConditionId": event.superseded_by_condition_id,
        }
        for event in events
    ]


@router.patch("/case-conditions/{condition_id}", response_model=CaseConditionResponse)
def revise_case_condition(
    condition_id: uuid.UUID,
    payload: ReviseCaseConditionRequest,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> CaseConditionResponse:
    view = service.revise(CaseConditionId(condition_id), content=_content_from_revise(payload))
    return CaseConditionResponse.from_domain(view)


@router.post(
    "/case-conditions/{condition_id}/evaluate", response_model=CaseConditionEvaluationResponse
)
def evaluate_case_condition(
    condition_id: uuid.UUID,
    payload: EvaluateCaseConditionRequest,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> CaseConditionEvaluationResponse:
    result = service.evaluate(
        CaseConditionId(condition_id),
        evaluated_at=payload.evaluated_at,
        observed_value=payload.observed_value,
        human_asserted_satisfied=payload.human_asserted_satisfied,
    )
    return CaseConditionEvaluationResponse.from_domain(result)


@router.post("/case-conditions/{condition_id}/retire", status_code=204, response_class=Response)
def retire_case_condition(
    condition_id: uuid.UUID,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> Response:
    service.retire(CaseConditionId(condition_id))
    return Response(status_code=204)


@router.post("/case-conditions/{condition_id}/supersede", response_model=CaseConditionResponse)
def supersede_case_condition(
    condition_id: uuid.UUID,
    payload: SupersedeCaseConditionRequest,
    service: CaseConditionService = Depends(get_case_condition_service),
) -> CaseConditionResponse:
    view = service.supersede(
        CaseConditionId(condition_id),
        superseded_by_condition_id=(
            str(payload.superseded_by_condition_id)
            if payload.superseded_by_condition_id is not None
            else None
        ),
    )
    return CaseConditionResponse.from_domain(view)
