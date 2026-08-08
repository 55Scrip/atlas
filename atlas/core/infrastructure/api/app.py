"""Composition root for the Atlas core API.

`create_app` is a factory (rather than a bare module-level `app`) so tests
can build isolated instances and override dependencies without touching
global state.
"""

from __future__ import annotations

from fastapi import FastAPI

from atlas.ai.api.router import router as discovery_chat_router
from atlas.alpha.case_intelligence.api.router import router as case_intelligence_router
from atlas.alpha.portfolio.api.router import router as alpha_portfolio_router
from atlas.alpha.portfolio_cockpit.api.router import router as portfolio_cockpit_router
from atlas.alpha.portfolio_intelligence.api.router import router as portfolio_intelligence_router
from atlas.alpha.portfolio_status.api.router import router as portfolio_status_router
from atlas.core.infrastructure.api.case.errors import (
    register_error_handlers as register_case_error_handlers,
)
from atlas.core.infrastructure.api.case.router import router as case_router
from atlas.core.infrastructure.api.decision.errors import (
    register_error_handlers as register_decision_error_handlers,
)
from atlas.core.infrastructure.api.decision.router import router as decision_router
from atlas.core.infrastructure.api.decision_context.errors import (
    register_error_handlers as register_decision_context_error_handlers,
)
from atlas.core.infrastructure.api.decision_context.router import (
    router as decision_context_router,
)
from atlas.core.infrastructure.api.evidence.errors import (
    register_error_handlers as register_evidence_error_handlers,
)
from atlas.core.infrastructure.api.evidence.router import router as evidence_router
from atlas.core.infrastructure.api.hypothesis.errors import (
    register_error_handlers as register_hypothesis_error_handlers,
)
from atlas.core.infrastructure.api.hypothesis.router import router as hypothesis_router
from atlas.core.infrastructure.api.judgment.errors import (
    register_error_handlers as register_judgment_error_handlers,
)
from atlas.core.infrastructure.api.judgment.router import router as judgment_router
from atlas.core.infrastructure.api.knowledge_reference.errors import (
    register_error_handlers as register_knowledge_reference_error_handlers,
)
from atlas.core.infrastructure.api.knowledge_reference.router import (
    router as knowledge_reference_router,
)
from atlas.core.infrastructure.api.observation.errors import (
    register_error_handlers as register_observation_error_handlers,
)
from atlas.core.infrastructure.api.observation.router import router as observation_router
from atlas.core.infrastructure.api.outcome.errors import (
    register_error_handlers as register_outcome_error_handlers,
)
from atlas.core.infrastructure.api.outcome.router import router as outcome_router
from atlas.core.infrastructure.api.reasoning_trace.errors import (
    register_error_handlers as register_reasoning_trace_error_handlers,
)
from atlas.core.infrastructure.api.reasoning_trace.router import router as reasoning_trace_router


def create_app() -> FastAPI:
    app = FastAPI(title="Atlas Core API")
    # Atlas Alpha, Sprint 1A: the one deliberate Core/Alpha composition
    # point. The router itself is authored and owned in `atlas/alpha/`,
    # not `atlas/core/` — this process serves both Core and provisional
    # Alpha routes, but `atlas/core/` never imports from `atlas/alpha/`
    # (enforced by tests/test_architecture_boundaries.py).
    app.include_router(alpha_portfolio_router)
    # ATLAS-015: the Portfolio Status report is a second, sibling
    # composition point with the same Alpha/Core boundary as the line
    # above -- authored and owned in `atlas/alpha/portfolio_status/`,
    # never imported back by `atlas/core/` outside this file.
    app.include_router(portfolio_status_router)
    # ATLAS-016: the Portfolio Intelligence report is a third, sibling
    # composition point -- authored and owned in
    # `atlas/alpha/portfolio_intelligence/`, the first live caller of the
    # canonical `atlas.decision_engine.pipeline`.
    app.include_router(portfolio_intelligence_router)
    # ATLAS-017: the Case Intelligence report is a fourth, sibling
    # composition point -- authored and owned in
    # `atlas/alpha/case_intelligence/`, running the same canonical
    # `atlas.decision_engine.pipeline` for a single Case instead of the
    # whole portfolio (via the shared
    # `atlas.alpha.portfolio_intelligence.pipeline_bridge` both modules
    # call).
    app.include_router(case_intelligence_router)
    # ATLAS-028: the Portfolio Cockpit report is a fifth, sibling
    # composition point -- authored and owned in
    # `atlas/alpha/portfolio_cockpit/`, composing many Cases at once via
    # `InvestmentCaseCompositionService.build_many` (ATLAS-027/028)
    # rather than re-deriving any analysis itself.
    app.include_router(portfolio_cockpit_router)
    # Discovery Intelligence v1: same pattern, one level removed — the
    # discovery-chat router is authored and owned in `atlas/ai/`, and is
    # itself `atlas/ai/`'s own one deliberate composition point with
    # `atlas/alpha/` (its provider-agnostic core, `discovery_chat.py`,
    # never imports `atlas.alpha` — enforced by
    # tests/test_architecture_boundaries.py).
    app.include_router(discovery_chat_router)
    app.include_router(case_router)
    app.include_router(decision_router)
    app.include_router(decision_context_router)
    app.include_router(observation_router)
    app.include_router(hypothesis_router)
    app.include_router(evidence_router)
    app.include_router(knowledge_reference_router)
    app.include_router(judgment_router)
    app.include_router(reasoning_trace_router)
    app.include_router(outcome_router)
    register_case_error_handlers(app)
    register_decision_error_handlers(app)
    register_decision_context_error_handlers(app)
    register_observation_error_handlers(app)
    register_hypothesis_error_handlers(app)
    register_evidence_error_handlers(app)
    register_knowledge_reference_error_handlers(app)
    register_judgment_error_handlers(app)
    register_reasoning_trace_error_handlers(app)
    register_outcome_error_handlers(app)
    return app


app = create_app()
