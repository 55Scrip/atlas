"""Composition root for the Atlas core API.

`create_app` is a factory (rather than a bare module-level `app`) so tests
can build isolated instances and override dependencies without touching
global state.
"""
from __future__ import annotations

from fastapi import FastAPI

from atlas.core.infrastructure.api.decision.errors import (
    register_error_handlers as register_decision_error_handlers,
)
from atlas.core.infrastructure.api.decision.router import router as decision_router


def create_app() -> FastAPI:
    app = FastAPI(title="Atlas Core API")
    app.include_router(decision_router)
    register_decision_error_handlers(app)
    return app


app = create_app()
