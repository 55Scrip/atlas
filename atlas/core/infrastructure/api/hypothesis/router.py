"""REST controller for Hypothesis Capture (API-004).

POST /hypotheses          - capture a new Hypothesis
GET  /hypotheses           - list every recorded Hypothesis, chronologically
GET  /hypotheses/{id}      - read a single Hypothesis

No filtering, no update, no patch, no delete.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from atlas.core.application.hypothesis.capture_hypothesis import (
    CaptureHypothesisRequest,
    HypothesisService,
)
from atlas.core.domain.hypothesis.value_objects import HypothesisId
from atlas.core.infrastructure.api.hypothesis.dependencies import get_hypothesis_service
from atlas.core.infrastructure.api.hypothesis.schemas import (
    CreateHypothesisRequest,
    HypothesisResponse,
)

router = APIRouter(prefix="/hypotheses", tags=["hypotheses"])


@router.post("", response_model=HypothesisResponse, status_code=201)
def create_hypothesis(
    payload: CreateHypothesisRequest,
    service: HypothesisService = Depends(get_hypothesis_service),
) -> HypothesisResponse:
    hypothesis = service.capture(
        CaptureHypothesisRequest(
            statement=payload.statement,
            formulated_at=payload.formulated_at,
            note=payload.note,
        )
    )
    return HypothesisResponse.from_domain(hypothesis)


@router.get("", response_model=list[HypothesisResponse])
def list_hypotheses(
    service: HypothesisService = Depends(get_hypothesis_service),
) -> list[HypothesisResponse]:
    return [HypothesisResponse.from_domain(h) for h in service.list_all()]


@router.get("/{hypothesis_id}", response_model=HypothesisResponse)
def get_hypothesis(
    hypothesis_id: uuid.UUID,
    service: HypothesisService = Depends(get_hypothesis_service),
) -> HypothesisResponse:
    hypothesis = service.get(HypothesisId(hypothesis_id))
    return HypothesisResponse.from_domain(hypothesis)
