"""REST controller for Reasoning Trace (DO-IMP-009).

POST   /reasoning-traces        - capture a new Reasoning Trace
GET    /reasoning-traces        - list every recorded Reasoning Trace
GET    /reasoning-traces/{id}   - read a single Reasoning Trace
DELETE /reasoning-traces/{id}   - remove a single Reasoning Trace

Atlas Alpha, Reasoning Trace Sprint 1: list and delete are new,
extending this package beyond its originally-approved scope
(docs/atlas_domain_object_architecture/
Reasoning-Trace-Implementation-Design.md, Section 31/38 originally
excluded both). See `atlas/core/domain/reasoning_trace/repository.py`'s
own docstring for why this extension was made and user-authorized.
Still no update or patch. `GET /reasoning-traces` returns every record;
a consuming client that needs only one Case's own Reasoning Traces
filters client-side by `caseId`, the same pattern already established
for Observation, Evidence, and Knowledge Reference.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response

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


@router.get("", response_model=list[ReasoningTraceResponse])
def list_reasoning_traces(
    service: ReasoningTraceService = Depends(get_reasoning_trace_service),
) -> list[ReasoningTraceResponse]:
    return [ReasoningTraceResponse.from_domain(r) for r in service.list_all()]


@router.get("/{reasoning_trace_id}", response_model=ReasoningTraceResponse)
def get_reasoning_trace(
    reasoning_trace_id: uuid.UUID,
    service: ReasoningTraceService = Depends(get_reasoning_trace_service),
) -> ReasoningTraceResponse:
    reasoning_trace = service.get(ReasoningTraceId(reasoning_trace_id))
    return ReasoningTraceResponse.from_domain(reasoning_trace)


@router.delete("/{reasoning_trace_id}", status_code=204, response_class=Response)
def delete_reasoning_trace(
    reasoning_trace_id: uuid.UUID,
    service: ReasoningTraceService = Depends(get_reasoning_trace_service),
) -> Response:
    service.delete(ReasoningTraceId(reasoning_trace_id))
    return Response(status_code=204)
