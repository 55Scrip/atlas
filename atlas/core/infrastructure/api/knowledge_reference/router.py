"""REST controller for Knowledge Reference (DO-IMP-003).

POST /knowledge-references        - capture a new Knowledge Reference
GET  /knowledge-references/{id}   - read a single Knowledge Reference

No list, update, patch, or delete: none is required by this package's
approved scope.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

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


@router.get("/{knowledge_reference_id}", response_model=KnowledgeReferenceResponse)
def get_knowledge_reference(
    knowledge_reference_id: uuid.UUID,
    service: KnowledgeReferenceService = Depends(get_knowledge_reference_service),
) -> KnowledgeReferenceResponse:
    knowledge_reference = service.get(KnowledgeReferenceId(knowledge_reference_id))
    return KnowledgeReferenceResponse.from_domain(knowledge_reference)
