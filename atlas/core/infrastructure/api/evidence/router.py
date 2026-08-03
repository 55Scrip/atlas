"""REST controller for Evidence Capture (API-005).

POST   /evidence          - capture a new Evidence record, anchored to an
                             existing Observation
GET    /evidence           - list every recorded Evidence, chronologically
GET    /evidence/{id}      - read a single Evidence record
DELETE /evidence/{id}      - remove a single Evidence record

Singular `/evidence` throughout — "evidence" is treated as an
uncountable noun in this domain and API naming, not `/evidences`.

Atlas Alpha, Evidence Sprint 1: DELETE is new — the first delete
capability anywhere in this API. Still no filtering, no update, no
patch. `GET /evidence` still returns every record; a consuming client
that needs only one Observation's own Evidence filters client-side by
`observationId`, the same pattern already established for `GET
/observations` and Case (Sprint 1, Commit 10).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

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
            observation_id=payload.observation_id,
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


@router.delete("/{evidence_id}", status_code=204, response_class=Response)
def delete_evidence(
    evidence_id: uuid.UUID,
    service: EvidenceService = Depends(get_evidence_service),
) -> Response:
    service.delete(EvidenceId(evidence_id))
    return Response(status_code=204)
