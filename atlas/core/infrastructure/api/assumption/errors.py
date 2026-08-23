"""Maps Assumption's own domain errors onto HTTP responses.

`atlas.core.domain.decision_context.exceptions.DecisionNotFoundError`
is deliberately not re-handled here — it already has its own app-wide
handler, registered once in `atlas.core.infrastructure.api.app`. Only
the exception types this package itself defines (or raises from
`assumption.exceptions`) are registered here — the same discipline
`case_condition/errors.py` already established (Sprint 10).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.assumption.exceptions import (
    AssumptionNotFoundError,
    AssumptionTerminatedError,
    CaseConditionNotFoundForLinkError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AssumptionNotFoundError)
    async def _handle_not_found(request: Request, exc: AssumptionNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AssumptionTerminatedError)
    async def _handle_terminated(
        request: Request, exc: AssumptionTerminatedError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(CaseConditionNotFoundForLinkError)
    async def _handle_case_condition_not_found(
        request: Request, exc: CaseConditionNotFoundForLinkError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
