"""REST controller for Evidence Capture (API-005).

POST /evidence          - capture a new Evidence record
GET  /evidence           - list every recorded Evidence, chronologically
GET  /evidence/{id}      - read a single Evidence record

Singular `/evidence` throughout — "evidence" is treated as an
uncountable noun in this domain and API naming, not `/evidences`.

No filtering, no update, no patch, no delete.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from atlas.core.application.evidence.capture_evidence import (
    CaptureEvidenceRequest,
    EvidenceService,
)
from atlas.core.domain.evidence.value_objects import EvidenceId
from atlas.core.infrastructure.api.evidence.dependencies import get_evidence_service
from atlas.core.infrastructure.api.evidence.schemas import (
    CreateEvidenceRequest,
    EvidenceResponse,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceResponse, status_code=201)
def create_evidence(
    payload: CreateEvidenceRequest,
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    evidence = service.capture(
        CaptureEvidenceRequest(
            statement=payload.statement,
            direction=payload.direction,
            observed_at=payload.observed_at,
            source=payload.source,
            note=payload.note,
        )
    )
    return EvidenceResponse.from_domain(evidence)


@router.get("", response_model=list[EvidenceResponse])
def list_evidence(
    service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceResponse]:
    return [EvidenceResponse.from_domain(e) for e in service.list_all()]


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    evidence_id: uuid.UUID,
    service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceResponse:
    evidence = service.get(EvidenceId(evidence_id))
    return EvidenceResponse.from_domain(evidence)
