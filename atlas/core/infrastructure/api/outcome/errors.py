"""Maps Outcome domain failures onto HTTP responses.

`OutcomeNotFoundError` (the Outcome itself not existing on GET) maps to
404. `DecisionNotFoundError` (the referenced Decision not existing on
POST) and `OutcomeValidationError` (missing statement, invalid
occurred_at) map to 400 — invalid input, not a server fault — matching
the convention already established for Evidence/Knowledge
Reference/Reasoning Trace/Judgment's own referenced-object and
validation errors. Malformed request *shape* (a required field missing
entirely) falls through to FastAPI's default 422, the same accepted
asymmetry already documented for every other module in this codebase.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.outcome.exceptions import (
    DecisionNotFoundError,
    OutcomeNotFoundError,
    OutcomeValidationError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OutcomeNotFoundError)
    async def _handle_not_found(request: Request, exc: OutcomeNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DecisionNotFoundError)
    async def _handle_decision_not_found(
        request: Request, exc: DecisionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(OutcomeValidationError)
    async def _handle_validation_error(
        request: Request, exc: OutcomeValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
