"""REST controller for Reasoning Trace (DO-IMP-009).

POST /reasoning-traces        - capture a new Reasoning Trace
GET  /reasoning-traces/{id}   - read a single Reasoning Trace

No list, update, patch, or delete: none is required by this package's
approved scope (docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 31).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from atlas.core.application.reasoning_trace.capture_reasoning_trace import (
    CaptureReasoningTraceRequest,
    ReasoningTraceService,
)
from atlas.core.domain.reasoning_trace.value_objects import ReasoningTraceId
from atlas.core.infrastructure.api.reasoning_trace.dependencies import (
    get_reasoning_trace_service,
)
from atlas.core.infrastructure.api.reasoning_trace.schemas import (
    CreateReasoningTraceRequest,
    ReasoningTraceResponse,
)

router = APIRouter(prefix="/reasoning-traces", tags=["reasoning-traces"])


@router.post("", response_model=ReasoningTraceResponse, status_code=201)
def create_reasoning_trace(
    payload: CreateReasoningTraceRequest,
    service: ReasoningTraceService = Depends(get_reasoning_trace_service),
) -> ReasoningTraceResponse:
    reasoning_trace = service.capture(
        CaptureReasoningTraceRequest(
            case_id=payload.case_id,
            supports=[support.to_domain() for support in payload.supports],
        )
    )
    return ReasoningTraceResponse.from_domain(reasoning_trace)


@router.get("/{reasoning_trace_id}", response_model=ReasoningTraceResponse)
def get_reasoning_trace(
    reasoning_trace_id: uuid.UUID,
    service: ReasoningTraceService = Depends(get_reasoning_trace_service),
) -> ReasoningTraceResponse:
    reasoning_trace = service.get(ReasoningTraceId(reasoning_trace_id))
    return ReasoningTraceResponse.from_domain(reasoning_trace)
