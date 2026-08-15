"""Composition root for the Atlas core API.

`create_app` is a factory (rather than a bare module-level `app`) so tests
can build isolated instances and override dependencies without touching
global state.
"""

from __future__ import annotations

from fastapi import FastAPI

from atlas.ai.api.router import router as discovery_chat_router
from atlas.alpha.case_intelligence.api.router import router as case_intelligence_router
from atlas.alpha.daily_brief.api.router import router as daily_brief_router
from atlas.alpha.investment_case.api.router import router as investment_case_router
from atlas.alpha.investment_case_history.api.router import router as investment_case_history_router
from atlas.alpha.observed_decision_properties.api.router import (
    router as observed_decision_properties_router,
)
from atlas.alpha.portfolio.api.router import router as alpha_portfolio_router
from atlas.alpha.portfolio_cockpit.api.router import router as portfolio_cockpit_router
from atlas.alpha.portfolio_intelligence.api.router import router as portfolio_intelligence_router
from atlas.alpha.portfolio_status.api.router import router as portfolio_status_router
from atlas.alpha.security_confirmation.api.errors import (
    register_error_handlers as register_security_confirmation_error_handlers,
)
from atlas.alpha.security_confirmation.api.router import router as security_confirmation_router
from atlas.alpha.security_discovery.api.router import router as security_discovery_router
from atlas.alpha.watchlist.api.router import router as alpha_watchlist_router
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
    # Investment Case Engine v1 slice: Watchlist is a sibling
    # composition point with the identical Alpha/Core boundary as
    # Portfolio above -- authored and owned in `atlas/alpha/watchlist/`,
    # giving Watchlist the same automatic Case-linkage and enrichment
    # Portfolio already has, per "Watchlist and Portfolio are membership
    # contexts around the same company knowledge."
    app.include_router(alpha_watchlist_router)
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
    # ATLAS-029: the canonical Investment Case analysis is a sibling
    # route under the same `/cases` prefix as `case_intelligence` above
    # -- authored and owned in `atlas/alpha/investment_case/`, powered
    # by `InvestmentCaseCompositionService.build` (ATLAS-027) rather
    # than a separate `decision_engine.run_pipeline` call. Additive:
    # `case_intelligence`'s own endpoint is untouched and still serves
    # `discovery_context` (ATLAS-029's own documented, deliberate gap).
    app.include_router(investment_case_router)
    # ATLAS-028: the Portfolio Cockpit report is a fifth, sibling
    # composition point -- authored and owned in
    # `atlas/alpha/portfolio_cockpit/`, composing many Cases at once via
    # `InvestmentCaseCompositionService.build_many` (ATLAS-027/028)
    # rather than re-deriving any analysis itself.
    app.include_router(portfolio_cockpit_router)
    # Daily Brief v1: a sixth, sibling composition point -- authored and
    # owned in `atlas/alpha/daily_brief/`, a pure distribution layer over
    # Investment Case Change Intelligence (composing every Portfolio
    # holding's and Watchlist entry's own `InvestmentCaseComposition
    # .change_intelligence` via `InvestmentCaseCompositionService.build`,
    # never recomputing analysis itself).
    app.include_router(daily_brief_router)
    # History v1: a seventh, sibling composition point -- authored and
    # owned in `atlas/alpha/investment_case_history/`, a read-only
    # presentation layer over the exact same persisted
    # `AnalyticalSnapshot`/`ChangeIntelligence` state Investment Case
    # Change Intelligence and Daily Brief already read (via
    # `SqlAlchemyInvestmentCaseSnapshotRepository.get_history`), never
    # `InvestmentCaseCompositionService.build`/`build_many` -- opening
    # History can never create a new snapshot.
    app.include_router(investment_case_history_router)
    # Discovery Intelligence v1: same pattern, one level removed — the
    # discovery-chat router is authored and owned in `atlas/ai/`, and is
    # itself `atlas/ai/`'s own one deliberate composition point with
    # `atlas/alpha/` (its provider-agnostic core, `discovery_chat.py`,
    # never imports `atlas.alpha` — enforced by
    # tests/test_architecture_boundaries.py).
    app.include_router(discovery_chat_router)
    app.include_router(case_router)
    app.include_router(decision_router)
    # Observed Decision Properties v1 (Sprint 13): the smallest read-only
    # projection over the real Decision repository -- authored and owned
    # in `atlas/alpha/observed_decision_properties/`, reusing
    # `atlas.core.application.pattern_recognition`'s existing, unmodified
    # strategies. Never computes or serves a Strategy Signature; see that
    # package's own `__init__.py` for the full Sprint 10-13 provenance.
    app.include_router(observed_decision_properties_router)
    # Security Confirmation v1 (Sprint 20): the narrow, decision-scoped
    # boundary between Sprint 19's read-only SecurityCandidate discovery
    # and a canonical SecurityIdentity Atlas has not built. Authored and
    # owned in `atlas/alpha/security_confirmation/` -- records only the
    # investor's own explicit assertion ("this Decision meant ticker
    # X"), never Decision.subject or any other historical field. See
    # that package's own `__init__.py` for the full ontology.
    app.include_router(security_confirmation_router)
    # Security Discovery v1 API (Sprint 21): the one read-only endpoint
    # exposing Sprint 19's already-verified discover_security_candidates
    # to a frontend caller. GET-only, no request body, no persistence,
    # no candidate is ever ranked or auto-selected -- see that
    # package's own `api/router.py` docstring.
    app.include_router(security_discovery_router)
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
    register_security_confirmation_error_handlers(app)
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
