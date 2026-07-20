"""REST controller for Case (DO-IMP-001).

POST /cases        - establish a new Case (no request body: Case has no
                      semantic input to capture, OE-002 §3.1)
GET  /cases/{id}   - read a single Case

No list, update, patch, or delete: none is required by this package's
approved scope.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from atlas.core.application.case.create_case import CaseService
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.infrastructure.api.case.dependencies import get_case_service
from atlas.core.infrastructure.api.case.schemas import CaseResponse

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=201)
def create_case(service: CaseService = Depends(get_case_service)) -> CaseResponse:
    case = service.create()
    return CaseResponse.from_domain(case)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    service: CaseService = Depends(get_case_service),
) -> CaseResponse:
    case = service.get(CaseId(case_id))
    return CaseResponse.from_domain(case)
