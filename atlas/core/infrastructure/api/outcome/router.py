"""REST controller for Outcome (ATLAS-001 Core Loop).

POST /outcomes        - capture a new Outcome of an existing Decision
GET  /outcomes        - list every recorded Outcome
GET  /outcomes/{id}   - read a single Outcome

Atlas Alpha, Outcome Sprint 1: this is Outcome's first REST API of any
kind. No update, patch, or delete: `OutcomeRepository` exposes only
`add`/`get`/`list_all`/`list_by_decision_id` — insert-only, matching the
already-authorized `Outcome-Implementation-Design.md`'s own "Delete:
forbidden" and the real, current repository's own docstring ("Insert-
only: no update, no delete"). `GET /outcomes` returns every record; a
consuming client that needs only one Case's own Outcomes filters
client-side by `caseId`, the same pattern already established for every
other module in this codebase.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from atlas.core.application.outcome.capture_outcome import CaptureOutcomeRequest, OutcomeService
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.core.infrastructure.api.outcome.dependencies import get_outcome_service
from atlas.core.infrastructure.api.outcome.schemas import CreateOutcomeRequest, OutcomeResponse

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("", response_model=OutcomeResponse, status_code=201)
def create_outcome(
    payload: CreateOutcomeRequest,
    service: OutcomeService = Depends(get_outcome_service),
) -> OutcomeResponse:
    outcome = service.capture(
        CaptureOutcomeRequest(
            decision_id=payload.decision_id,
            statement=payload.statement,
            occurred_at=payload.occurred_at,
            note=payload.note,
        )
    )
    return OutcomeResponse.from_domain(outcome)


@router.get("", response_model=list[OutcomeResponse])
def list_outcomes(
    service: OutcomeService = Depends(get_outcome_service),
) -> list[OutcomeResponse]:
    return [OutcomeResponse.from_domain(o) for o in service.list_all()]


@router.get("/{outcome_id}", response_model=OutcomeResponse)
def get_outcome(
    outcome_id: uuid.UUID,
    service: OutcomeService = Depends(get_outcome_service),
) -> OutcomeResponse:
    outcome = service.get(OutcomeId(outcome_id))
    return OutcomeResponse.from_domain(outcome)
