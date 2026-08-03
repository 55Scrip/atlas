"""REST controller for Knowledge Reference (DO-IMP-003).

POST   /knowledge-references        - capture a new Knowledge Reference
GET    /knowledge-references        - list every recorded Knowledge Reference
GET    /knowledge-references/{id}   - read a single Knowledge Reference
DELETE /knowledge-references/{id}   - remove a single Knowledge Reference

Atlas Alpha, Knowledge Reference Sprint 1: list and delete are new,
mirroring Evidence's own identical additions in Evidence Sprint 1. Still
no update or patch. `GET /knowledge-references` returns every record; a
consuming client that needs only one Case's own Knowledge References
filters client-side by `caseId`, the same pattern already established
for Observation (Sprint 1, Commit 10) and Evidence.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

from atlas.core.application.knowledge_reference.capture_knowledge_reference import (
    CaptureKnowledgeReferenceRequest,
    KnowledgeReferenceService,
)
from atlas.core.domain.knowledge_reference.value_objects import KnowledgeReferenceId
from atlas.core.infrastructure.api.knowledge_reference.dependencies import (
    get_knowledge_reference_service,
)
from atlas.core.infrastructure.api.knowledge_reference.schemas import (
    CreateKnowledgeReferenceRequest,
    KnowledgeReferenceResponse,
)

router = APIRouter(prefix="/knowledge-references", tags=["knowledge-references"])


@router.post("", response_model=KnowledgeReferenceResponse, status_code=201)
def create_knowledge_reference(
    payload: CreateKnowledgeReferenceRequest,
    service: KnowledgeReferenceService = Depends(get_knowledge_reference_service),
) -> KnowledgeReferenceResponse:
    knowledge_reference = service.capture(
        CaptureKnowledgeReferenceRequest(
            case_id=payload.case_id,
            target_type=payload.target.target_type,
            target_id=payload.target.target_id,
        )
    )
    return KnowledgeReferenceResponse.from_domain(knowledge_reference)


@router.get("", response_model=list[KnowledgeReferenceResponse])
def list_knowledge_references(
    service: KnowledgeReferenceService = Depends(get_knowledge_reference_service),
) -> list[KnowledgeReferenceResponse]:
    return [KnowledgeReferenceResponse.from_domain(k) for k in service.list_all()]


@router.get("/{knowledge_reference_id}", response_model=KnowledgeReferenceResponse)
def get_knowledge_reference(
    knowledge_reference_id: uuid.UUID,
    service: KnowledgeReferenceService = Depends(get_knowledge_reference_service),
) -> KnowledgeReferenceResponse:
    knowledge_reference = service.get(KnowledgeReferenceId(knowledge_reference_id))
    return KnowledgeReferenceResponse.from_domain(knowledge_reference)


@router.delete("/{knowledge_reference_id}", status_code=204, response_class=Response)
def delete_knowledge_reference(
    knowledge_reference_id: uuid.UUID,
    service: KnowledgeReferenceService = Depends(get_knowledge_reference_service),
) -> Response:
    service.delete(KnowledgeReferenceId(knowledge_reference_id))
    return Response(status_code=204)
