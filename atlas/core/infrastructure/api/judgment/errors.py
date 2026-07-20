"""Maps Judgment domain failures onto HTTP responses.

Invalid input (target not found, cross-Case target, currently
unavailable target type) maps to 400, matching Knowledge Reference's
own established convention. `JudgmentNotFoundError` (the Judgment
itself not existing on GET) maps to 404. Malformed request *shape* (a
required field missing entirely, or a `targetType` outside the six
adopted values, which Pydantic rejects before this service is ever
reached) falls through to FastAPI's default 422, the same accepted
asymmetry already documented for every other module in this codebase.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.judgment.exceptions import (
    CrossCaseTargetError,
    JudgmentNotFoundError,
    MissingCharacterizationError,
    TargetNotFoundError,
    TargetTypeUnavailableError,
)
from atlas.core.domain.shared.exceptions import (
    InvalidTypedDomainObjectReferenceError,
    UnknownDomainObjectTypeError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(JudgmentNotFoundError)
    async def _handle_not_found(request: Request, exc: JudgmentNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MissingCharacterizationError)
    async def _handle_missing_characterization(
        request: Request, exc: MissingCharacterizationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(TargetNotFoundError)
    async def _handle_target_not_found(request: Request, exc: TargetNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(CrossCaseTargetError)
    async def _handle_cross_case(request: Request, exc: CrossCaseTargetError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(TargetTypeUnavailableError)
    async def _handle_target_type_unavailable(
        request: Request, exc: TargetTypeUnavailableError
    ) -> JSONResponse:
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
