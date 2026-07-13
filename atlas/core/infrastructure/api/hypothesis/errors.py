"""Maps Hypothesis domain failures onto HTTP responses.

Per API-004: invalid input maps to 400 (matching API-002/API-003's
convention, not API-001's 422) — the spec's own instruction, not a new
inconsistency introduced here. The spec's "error code equivalent to
INVALID_HYPOTHESIS" is realized as the `HypothesisValidationError`
exception class itself (and its more specific subclasses,
`MissingStatementError` / `InvalidFormulatedAtError`), not as an added
`code` field on the JSON body — the spec also says not to redesign the
repository-wide error contract in this increment, and every other Atlas
core endpoint returns the plain `{"detail": "<message>"}` shape. Malformed
request *shape* (a required field missing entirely) still falls through
to FastAPI's default 422, same accepted asymmetry already documented for
API-002/API-003.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.hypothesis.exceptions import (
    HypothesisNotFoundError,
    HypothesisValidationError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HypothesisValidationError)
    async def _handle_validation_error(
        request: Request, exc: HypothesisValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(HypothesisNotFoundError)
    async def _handle_not_found(
        request: Request, exc: HypothesisNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
