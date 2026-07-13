"""Maps DecisionContext domain failures onto HTTP responses.

Deliberately separate from atlas.core.infrastructure.api.decision.errors:
API-002 specifies different status codes (400 for invalid context, where
API-001 uses 422) and this module only ever registers handlers for
DecisionContext's own exception types, so API-001's existing behavior is
untouched.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.decision_context.exceptions import (
    DecisionContextValidationError,
    DecisionNotFoundError,
    DuplicateDecisionContextError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DecisionContextValidationError)
    async def _handle_validation_error(
        request: Request, exc: DecisionContextValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(DecisionNotFoundError)
    async def _handle_decision_not_found(
        request: Request, exc: DecisionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DuplicateDecisionContextError)
    async def _handle_duplicate_context(
        request: Request, exc: DuplicateDecisionContextError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
