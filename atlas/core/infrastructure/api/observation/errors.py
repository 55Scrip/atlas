"""Maps Observation domain failures onto HTTP responses.

Per API-003: invalid input maps to 400 (matching API-002's convention,
not API-001's 422) — the spec's own instruction, not a new inconsistency
introduced here. Malformed request *shape* (a required field missing
entirely) still falls through to FastAPI's default 422, same accepted
asymmetry already documented for API-002.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.observation.exceptions import ObservationValidationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ObservationValidationError)
    async def _handle_validation_error(
        request: Request, exc: ObservationValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
