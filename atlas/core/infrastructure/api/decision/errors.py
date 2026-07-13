"""Maps domain validation failures onto HTTP responses.

This is the only place that knows Decision's domain errors map to 422 — the
router stays free of try/except noise.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.decision.exceptions import DecisionValidationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DecisionValidationError)
    async def _handle_decision_validation_error(
        request: Request, exc: DecisionValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def _handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
