"""Maps Security Confirmation's own domain errors onto HTTP responses.
Mirrors `atlas.core.infrastructure.api.decision.errors`'s own
one-error-type-per-handler shape."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.alpha.security_confirmation.exceptions import (
    ConflictingConfirmationError,
    DecisionNotFoundError,
    UnsupportedDiscoverySourceError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DecisionNotFoundError)
    async def _handle_decision_not_found(request: Request, exc: DecisionNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(UnsupportedDiscoverySourceError)
    async def _handle_unsupported_source(
        request: Request, exc: UnsupportedDiscoverySourceError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ConflictingConfirmationError)
    async def _handle_conflicting_confirmation(
        request: Request, exc: ConflictingConfirmationError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
