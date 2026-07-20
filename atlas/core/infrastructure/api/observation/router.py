"""REST controller for Observation Capture (API-003).

POST /observations       - capture a new Observation
GET  /observations        - list every recorded Observation
GET  /observations/{id}   - read a single Observation

No filtering, no update, no patch, no delete.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from atlas.core.application.observation.capture_observation import (
    CaptureObservationRequest,
    CaptureObservationService,
)
from atlas.core.domain.observation.repository import ObservationRepository
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.api.observation.dependencies import (
    get_capture_observation_service,
    get_observation_repository,
)
from atlas.core.infrastructure.api.observation.schemas import (
    CreateObservationRequest,
    ObservationResponse,
)

router = APIRouter(prefix="/observations", tags=["observations"])


@router.post("", response_model=ObservationResponse, status_code=201)
def create_observation(
    payload: CreateObservationRequest,
    service: CaptureObservationService = Depends(get_capture_observation_service),
) -> ObservationResponse:
    observation = service.capture(
        CaptureObservationRequest(
            case_id=payload.case_id,
            subject=payload.subject,
            statement=payload.statement,
            observed_at=payload.observed_at,
            source=payload.source,
            note=payload.note,
        )
    )
    return ObservationResponse.from_domain(observation)


@router.get("", response_model=list[ObservationResponse])
def list_observations(
    repository: ObservationRepository = Depends(get_observation_repository),
) -> list[ObservationResponse]:
    return [ObservationResponse.from_domain(o) for o in repository.list_all()]


@router.get("/{observation_id}", response_model=ObservationResponse)
def get_observation(
    observation_id: uuid.UUID,
    repository: ObservationRepository = Depends(get_observation_repository),
) -> ObservationResponse:
    observation = repository.get(ObservationId(observation_id))
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return ObservationResponse.from_domain(observation)
