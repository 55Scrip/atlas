"""Maps Evidence domain failures onto HTTP responses.

Per API-005: invalid input maps to 400 (matching API-002/API-003/API-004's
convention, not API-001's 422) — the spec's own instruction, not a new
inconsistency introduced here. Malformed request *shape* (a required
field missing entirely) still falls through to FastAPI's default 422,
same accepted asymmetry already documented for API-002/003/004.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.evidence.exceptions import EvidenceNotFoundError, EvidenceValidationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(EvidenceValidationError)
    async def _handle_validation_error(
        request: Request, exc: EvidenceValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(EvidenceNotFoundError)
    async def _handle_not_found(request: Request, exc: EvidenceNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
