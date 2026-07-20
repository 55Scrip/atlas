"""REST controller for Judgment (DO-IMP-004).

POST /judgments        - capture a new Judgment
GET  /judgments/{id}   - read a single Judgment

No list, update, patch, or delete: none is required by this package's
approved scope.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from atlas.core.application.judgment.capture_judgment import (
    CaptureJudgmentRequest,
    JudgmentService,
)
from atlas.core.domain.judgment.value_objects import JudgmentId
from atlas.core.infrastructure.api.judgment.dependencies import get_judgment_service
from atlas.core.infrastructure.api.judgment.schemas import (
    CreateJudgmentRequest,
    JudgmentResponse,
)

router = APIRouter(prefix="/judgments", tags=["judgments"])


@router.post("", response_model=JudgmentResponse, status_code=201)
def create_judgment(
    payload: CreateJudgmentRequest,
    service: JudgmentService = Depends(get_judgment_service),
) -> JudgmentResponse:
    judgment = service.capture(
        CaptureJudgmentRequest(
            case_id=payload.case_id,
            characterization=payload.characterization,
            subject=payload.subject.to_domain() if payload.subject is not None else None,
        )
    )
    return JudgmentResponse.from_domain(judgment)


@router.get("/{judgment_id}", response_model=JudgmentResponse)
def get_judgment(
    judgment_id: uuid.UUID,
    service: JudgmentService = Depends(get_judgment_service),
) -> JudgmentResponse:
    judgment = service.get(JudgmentId(judgment_id))
    return JudgmentResponse.from_domain(judgment)
