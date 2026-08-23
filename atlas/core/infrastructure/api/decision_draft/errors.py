"""Maps DecisionDraft's own domain errors onto HTTP responses.

`atlas.core.domain.case.exceptions.CaseNotFoundError`,
`atlas.core.domain.decision.exceptions.DecisionValidationError` (422),
and `atlas.core.domain.decision_context.exceptions
.DecisionContextValidationError` (400) are deliberately not re-handled
here — each already has its own app-wide handler, registered once in
`atlas.core.infrastructure.api.app`, and `DecisionDraftService.commit()`
lets those exceptions propagate unmodified (see
`decision_draft_service.py`'s own docstring). Only the four exception
types this package itself defines are registered here.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.decision_draft.exceptions import (
    DecisionDraftAlreadyAbandonedError,
    DecisionDraftAlreadyCommittedError,
    DecisionDraftConflictError,
    DecisionDraftNotFoundError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DecisionDraftNotFoundError)
    async def _handle_not_found(
        request: Request, exc: DecisionDraftNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DecisionDraftAlreadyAbandonedError)
    async def _handle_already_abandoned(
        request: Request, exc: DecisionDraftAlreadyAbandonedError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DecisionDraftAlreadyCommittedError)
    async def _handle_already_committed(
        request: Request, exc: DecisionDraftAlreadyCommittedError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DecisionDraftConflictError)
    async def _handle_conflict(
        request: Request, exc: DecisionDraftConflictError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
