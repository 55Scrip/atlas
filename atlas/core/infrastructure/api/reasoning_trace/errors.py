"""Maps Reasoning Trace domain failures onto HTTP responses.

`ReasoningTraceNotFoundError` (the Reasoning Trace itself not existing
on GET) maps to 404. `EmptySupportError`, `TargetNotFoundError`, and
`CrossCaseTargetError` map to 400, matching Knowledge Reference's own
established convention: invalid input, not a server fault. Malformed
request *shape* (a required field missing entirely, or a `targetType`
outside the six adopted values, which Pydantic rejects before this
service is ever reached) falls through to FastAPI's default 422, the
same accepted asymmetry already documented for every other module in
this codebase.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.reasoning_trace.exceptions import (
    CrossCaseTargetError,
    EmptySupportError,
    ReasoningTraceNotFoundError,
    TargetNotFoundError,
)
from atlas.core.domain.shared.exceptions import (
    InvalidTypedDomainObjectReferenceError,
    UnknownDomainObjectTypeError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ReasoningTraceNotFoundError)
    async def _handle_not_found(
        request: Request, exc: ReasoningTraceNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(EmptySupportError)
    async def _handle_empty_support(request: Request, exc: EmptySupportError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(TargetNotFoundError)
    async def _handle_target_not_found(request: Request, exc: TargetNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(CrossCaseTargetError)
    async def _handle_cross_case(request: Request, exc: CrossCaseTargetError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(UnknownDomainObjectTypeError)
    async def _handle_unknown_type(
        request: Request, exc: UnknownDomainObjectTypeError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(InvalidTypedDomainObjectReferenceError)
    async def _handle_invalid_reference(
        request: Request, exc: InvalidTypedDomainObjectReferenceError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
