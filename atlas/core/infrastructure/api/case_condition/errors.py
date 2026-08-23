"""Maps CaseCondition's own domain errors onto HTTP responses.

`CaseNotFoundError` and `atlas.core.domain.decision_context.exceptions
.DecisionNotFoundError` are deliberately not re-handled here — each
already has its own app-wide handler, registered once in
`atlas.core.infrastructure.api.app`. Only the exception types this
package itself defines (or raises from `case_condition.exceptions`)
are registered here — the same discipline `decision_draft/errors.py`
already established (Sprint 9).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.core.domain.case_condition.exceptions import (
    CaseConditionNotFoundError,
    CaseConditionTerminatedError,
    ConditionNotMechanicallyEvaluableError,
    CrossCaseDecisionError,
    MissingObservedValueError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(CaseConditionNotFoundError)
    async def _handle_not_found(
        request: Request, exc: CaseConditionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(CaseConditionTerminatedError)
    async def _handle_terminated(
        request: Request, exc: CaseConditionTerminatedError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(CrossCaseDecisionError)
    async def _handle_cross_case(request: Request, exc: CrossCaseDecisionError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ConditionNotMechanicallyEvaluableError)
    async def _handle_not_evaluable(
        request: Request, exc: ConditionNotMechanicallyEvaluableError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(MissingObservedValueError)
    async def _handle_missing_observed_value(
        request: Request, exc: MissingObservedValueError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
