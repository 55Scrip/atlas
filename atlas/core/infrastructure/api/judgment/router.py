"""REST controller for Judgment (DO-IMP-004).

POST   /judgments        - capture a new Judgment
GET    /judgments        - list every recorded Judgment
GET    /judgments/{id}   - read a single Judgment
DELETE /judgments/{id}   - remove a single Judgment

Atlas Alpha, Judgment Sprint 1: list and delete are new, extending this
package beyond its originally-approved scope
(docs/atlas_domain_object_architecture/Judgment-Implementation-Design.md,
Section 32 originally stated "Delete: forbidden"). See
`atlas/core/domain/judgment/repository.py`'s own docstring for why this
extension was made and user-authorized. Still no update or patch.
`GET /judgments` returns every record; a consuming client that needs
only one Case's own Judgments filters client-side by `caseId`, the same
pattern already established for Observation, Evidence, Knowledge
Reference, and Reasoning Trace.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

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


@router.get("", response_model=list[JudgmentResponse])
def list_judgments(
    service: JudgmentService = Depends(get_judgment_service),
) -> list[JudgmentResponse]:
    return [JudgmentResponse.from_domain(j) for j in service.list_all()]


@router.get("/{judgment_id}", response_model=JudgmentResponse)
def get_judgment(
    judgment_id: uuid.UUID,
    service: JudgmentService = Depends(get_judgment_service),
) -> JudgmentResponse:
    judgment = service.get(JudgmentId(judgment_id))
    return JudgmentResponse.from_domain(judgment)


@router.delete("/{judgment_id}", status_code=204, response_class=Response)
def delete_judgment(
    judgment_id: uuid.UUID,
    service: JudgmentService = Depends(get_judgment_service),
) -> Response:
    service.delete(JudgmentId(judgment_id))
    return Response(status_code=204)
