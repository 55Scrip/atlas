"""Maps Case domain failures onto HTTP responses.

Only `CaseNotFoundError` is registered: Case has no user-supplied
semantic content, so no CaseValidationError exists to map (see
atlas/core/domain/case/exceptions.py). Malformed request shape (e.g. a
non-UUID path segment) falls through to FastAPI's default 422, the same
accepted convention already documented for every other module in this
codebase.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.case.exceptions import CaseNotFoundError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(CaseNotFoundError)
    async def _handle_not_found(request: Request, exc: CaseNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
