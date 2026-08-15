"""Maps Security Identity Evidence's own domain errors onto HTTP
responses. Mirrors `security_confirmation.api.errors`'s own
one-error-type-per-handler shape."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from atlas.alpha.security_identity_evidence.exceptions import NoActiveConfirmationError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NoActiveConfirmationError)
    async def _handle_no_active_confirmation(
        request: Request, exc: NoActiveConfirmationError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
