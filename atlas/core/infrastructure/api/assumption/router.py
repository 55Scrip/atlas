"""REST controller for Assumption (ADR-AS-001).

POST   /decisions/{decision_id}/assumptions                                  - create a new assumption
GET    /decisions/{decision_id}/assumptions                                  - list assumptions for a Decision
GET    /cases/{case_id}/assumptions                                          - list assumptions for a Case
GET    /assumptions/{assumption_id}                                          - read one assumption's current state
GET    /assumptions/{assumption_id}/events                                    - full event history
PATCH  /assumptions/{assumption_id}                                          - revise an assumption's content
POST   /assumptions/{assumption_id}/challenge                                 - record a challenge (or invalidation)
POST   /assumptions/{assumption_id}/retire                                    - retire (idempotent, terminal)
POST   /assumptions/{assumption_id}/supersede                                 - supersede (terminal)
POST   /assumptions/{assumption_id}/case-conditions/{condition_id}/attach     - link a CaseCondition (idempotent)
POST   /assumptions/{assumption_id}/case-conditions/{condition_id}/detach     - unlink a CaseCondition (idempotent)

No `DELETE` endpoint anywhere, deliberately — nothing this package
writes is ever actually deleted, matching the same, already-disclosed
convention `security_confirmation/api/router.py` states explicitly for
the identical reason ("a DELETE verb would misdescribe what revoke
really does"): `detach` appends a new `revised` event removing one
cross-reference from the current set, it does not erase anything.

Routes and conventions mirror `case_condition/router.py` (Sprint 10)
directly.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

from atlas.core.application.assumption.assumption_service import (
    AssumptionContent,
    AssumptionService,
)
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.api.assumption.dependencies import get_assumption_service
from atlas.core.infrastructure.api.assumption.schemas import (
    AssumptionResponse,
    ChallengeAssumptionRequest,
    CreateAssumptionRequest,
    ReviseAssumptionRequest,
    SupersedeAssumptionRequest,
)

router = APIRouter(tags=["assumptions"])


@router.post(
    "/decisions/{decision_id}/assumptions", response_model=AssumptionResponse, status_code=201
)
def create_assumption(
    decision_id: uuid.UUID,
    payload: CreateAssumptionRequest,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.create(
        decision_id=DecisionId(decision_id),
        content=AssumptionContent(statement=payload.statement, authorship=payload.authorship),
    )
    return AssumptionResponse.from_domain(view)


@router.get("/decisions/{decision_id}/assumptions", response_model=list[AssumptionResponse])
def list_assumptions_for_decision(
    decision_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> list[AssumptionResponse]:
    views = service.list_for_decision(DecisionId(decision_id))
    return [AssumptionResponse.from_domain(view) for view in views]


@router.get("/cases/{case_id}/assumptions", response_model=list[AssumptionResponse])
def list_assumptions_for_case(
    case_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> list[AssumptionResponse]:
    views = service.list_for_case(CaseId(case_id))
    return [AssumptionResponse.from_domain(view) for view in views]


@router.get("/assumptions/{assumption_id}", response_model=AssumptionResponse)
def get_assumption(
    assumption_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.read(AssumptionId(assumption_id))
    return AssumptionResponse.from_domain(view)


@router.get("/assumptions/{assumption_id}/events")
def list_assumption_events(
    assumption_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> list[dict]:
    events = service.list_events(AssumptionId(assumption_id))
    return [
        {
            "id": event.id,
            "eventType": event.event_type,
            "recordedAt": event.recorded_at.isoformat(),
            "severity": event.severity,
            "supersededByAssumptionId": event.superseded_by_assumption_id,
        }
        for event in events
    ]


@router.patch("/assumptions/{assumption_id}", response_model=AssumptionResponse)
def revise_assumption(
    assumption_id: uuid.UUID,
    payload: ReviseAssumptionRequest,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.revise(
        AssumptionId(assumption_id),
        content=AssumptionContent(statement=payload.statement, authorship=payload.authorship),
    )
    return AssumptionResponse.from_domain(view)


@router.post("/assumptions/{assumption_id}/challenge", response_model=AssumptionResponse)
def challenge_assumption(
    assumption_id: uuid.UUID,
    payload: ChallengeAssumptionRequest,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.challenge(
        AssumptionId(assumption_id),
        evidence_id=payload.evidence_id,
        note=payload.note,
        severity=payload.severity,
    )
    return AssumptionResponse.from_domain(view)


@router.post("/assumptions/{assumption_id}/retire", status_code=204, response_class=Response)
def retire_assumption(
    assumption_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> Response:
    service.retire(AssumptionId(assumption_id))
    return Response(status_code=204)


@router.post("/assumptions/{assumption_id}/supersede", response_model=AssumptionResponse)
def supersede_assumption(
    assumption_id: uuid.UUID,
    payload: SupersedeAssumptionRequest,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.supersede(
        AssumptionId(assumption_id),
        superseded_by_assumption_id=(
            str(payload.superseded_by_assumption_id)
            if payload.superseded_by_assumption_id is not None
            else None
        ),
    )
    return AssumptionResponse.from_domain(view)


@router.post(
    "/assumptions/{assumption_id}/case-conditions/{condition_id}/attach",
    response_model=AssumptionResponse,
)
def attach_case_condition(
    assumption_id: uuid.UUID,
    condition_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.attach_case_condition(AssumptionId(assumption_id), CaseConditionId(condition_id))
    return AssumptionResponse.from_domain(view)


@router.post(
    "/assumptions/{assumption_id}/case-conditions/{condition_id}/detach",
    response_model=AssumptionResponse,
)
def detach_case_condition(
    assumption_id: uuid.UUID,
    condition_id: uuid.UUID,
    service: AssumptionService = Depends(get_assumption_service),
) -> AssumptionResponse:
    view = service.detach_case_condition(AssumptionId(assumption_id), CaseConditionId(condition_id))
    return AssumptionResponse.from_domain(view)
