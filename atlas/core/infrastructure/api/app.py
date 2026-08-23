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
from atlas.alpha.portfolio_fit.api.router import router as portfolio_fit_router
from atlas.alpha.daily_brief_agenda.api.router import router as daily_brief_agenda_router
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
from atlas.alpha.stance.api.router import router as stance_router
from atlas.alpha.explainability.api.router import router as explainability_router
from atlas.alpha.evidence_quality.api.router import router as evidence_quality_router
from atlas.alpha.evidence_timeline.api.router import router as evidence_timeline_router
from atlas.alpha.materiality.api.router import router as materiality_router
from atlas.alpha.monitoring.api.router import router as monitoring_router
from atlas.alpha.ingestion.api.router import router as ingestion_router
from atlas.alpha.knowledge_orchestration.api.router import router as knowledge_orchestration_router
from atlas.alpha.knowledge_strategy.api.router import router as knowledge_strategy_router
from atlas.alpha.evidence_graph.api.router import router as evidence_graph_router
from atlas.alpha.decision_readiness.api.router import router as decision_readiness_router
from atlas.alpha.investment_decision.api.router import router as investment_decision_router
from atlas.alpha.recommendation_conviction.api.router import router as recommendation_conviction_router
from atlas.alpha.decision_path.api.router import router as decision_path_router
from atlas.alpha.opportunity_cost.api.router import router as opportunity_cost_router
from atlas.alpha.decision_explanation.api.router import router as decision_explanation_router
from atlas.alpha.decision_reliability.api.router import router as decision_reliability_router
from atlas.alpha.portfolio_decision.api.router import router as portfolio_decision_router
from atlas.alpha.decision_memory.api.router import router as decision_memory_router
from atlas.alpha.security_identity_evidence.api.errors import (
    register_error_handlers as register_security_identity_evidence_error_handlers,
)
from atlas.alpha.security_identity_evidence.api.router import router as security_identity_evidence_router
from atlas.alpha.watchlist.api.router import router as alpha_watchlist_router
from atlas.core.infrastructure.api.assumption.errors import (
    register_error_handlers as register_assumption_error_handlers,
)
from atlas.core.infrastructure.api.assumption.router import router as assumption_router
from atlas.core.infrastructure.api.case.errors import (
    register_error_handlers as register_case_error_handlers,
)
from atlas.core.infrastructure.api.case.router import router as case_router
from atlas.core.infrastructure.api.case_condition.errors import (
    register_error_handlers as register_case_condition_error_handlers,
)
from atlas.core.infrastructure.api.case_condition.router import router as case_condition_router
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
from atlas.core.infrastructure.api.decision_draft.errors import (
    register_error_handlers as register_decision_draft_error_handlers,
)
from atlas.core.infrastructure.api.decision_draft.router import router as decision_draft_router
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
from atlas.core.infrastructure.api.reasoning_workspace.router import (
    router as reasoning_workspace_router,
)


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
    # Portfolio Fit Engine (Product Sprint 4): an Alpha-layer
    # *interpretation*, not a new source of truth -- authored and owned in
    # `atlas/alpha/portfolio_fit/`, composing `InvestmentCaseComposition
    # .canonical_analysis` and `AlphaPortfolioState` (both unmodified) into
    # a deterministic, qualitative Portfolio Fit assessment. Stores
    # nothing of its own; see that package's own `__init__.py`.
    app.include_router(portfolio_fit_router)
    # Daily Brief Agenda / Priority Engine (Product Sprint 6): a further
    # Alpha-layer orchestration -- authored and owned in `atlas/alpha
    # /daily_brief_agenda/`, composing Change Intelligence, Portfolio
    # Fit, Portfolio Status, Portfolio Intelligence, Case Condition, and
    # Assumption (all six unmodified) into one deterministic,
    # qualitatively-prioritized agenda. Owns no business logic beyond
    # priority mapping and per-ticker consolidation; see that package's
    # own `__init__.py`.
    app.include_router(daily_brief_agenda_router)
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
    # Security Identity Evidence v1 (Sprint 23): the one explicit
    # "check external evidence" action layered over Sprint 20/22's own
    # confirmation lifecycle -- authored and owned in
    # `atlas/alpha/security_identity_evidence/`, never triggered
    # automatically by confirm/correct/revoke. See that package's own
    # `__init__.py` for the full ontology separating this from
    # SecurityCandidate, ConfirmedSecuritySelection, and the still-
    # unbuilt SecurityIdentity.
    app.include_router(security_identity_evidence_router)
    app.include_router(decision_context_router)
    # ADR-DD-001 (Sprint 9): DecisionDraft, the Case-scoped, event-sourced
    # save-and-resume aggregate for the Decision Workspace. Authored and
    # owned in `atlas/core/`, following Decision/DecisionContext's own
    # layering exactly -- see DecisionDraft-Implementation-Design.md.
    app.include_router(decision_draft_router)
    # ADR-CC-001 (Sprint 10): CaseCondition, the Case-scoped, event-sourced
    # Monitoring/Invalidation Condition aggregate. Authored and owned in
    # `atlas/core/`, following DecisionDraft's own layering exactly.
    app.include_router(case_condition_router)
    # ADR-AS-001 (Sprint 11): Assumption, the Decision-anchored,
    # event-sourced premise-tracking aggregate. Authored and owned in
    # `atlas/core/`, reusing CaseCondition's own event-stream pattern.
    app.include_router(assumption_router)
    app.include_router(observation_router)
    app.include_router(hypothesis_router)
    app.include_router(evidence_router)
    app.include_router(knowledge_reference_router)
    app.include_router(judgment_router)
    app.include_router(reasoning_trace_router)
    # Sprint 12: Reasoning Workspace orchestration -- composes Decision,
    # DecisionContext, DecisionDraft, Assumption, and CaseCondition via
    # their own existing services. Introduces no new domain entity, no
    # new table, no new exception type of its own (see that package's
    # own router docstring for why it has no dedicated errors.py).
    app.include_router(reasoning_workspace_router)
    app.include_router(outcome_router)
    # Atlas Intelligence Sprint 2 (Recommendation Quality & Actionability)
    # -- composes Investment Case + Portfolio Fit + Coverage, mirroring
    # `portfolio_fit_router`'s own composition-only shape.
    app.include_router(stance_router)
    # Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
    # Trace) -- composes Investment Case + Portfolio Fit + Coverage +
    # Stance, mirroring `stance_router`'s own composition-only shape.
    app.include_router(explainability_router)
    # Atlas Intelligence Sprint 4 (Evidence Quality & Conflict
    # Resolution) -- composes Investment Case + the raw BusinessRecord
    # repository directly (the one input `InvestmentCaseComposition`
    # does not itself expose), mirroring `stance_router`'s own
    # composition-only shape.
    app.include_router(evidence_quality_router)
    # Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
    # Understanding) -- a new, durable snapshot store for Coverage/
    # Stance/Evidence Quality (captured as a side effect of
    # `/cases/{case_id}/analysis`), plus a read-only cross-Case feed.
    app.include_router(evidence_timeline_router)
    # Atlas Intelligence -- Materiality & Priority Engine -- composes
    # Investment Case + Portfolio Fit + Coverage + Stance +
    # Explainability, mirroring `explainability_router`'s own
    # composition-only shape.
    app.include_router(materiality_router)
    # Atlas Intelligence Sprint 7 (Monitoring & Change Detection) --
    # `POST /monitoring/run`, an explicit, deterministic evaluation of
    # every Portfolio/Watchlist Case (never a scheduler); `GET
    # /monitoring/results`, its own read-model cache.
    app.include_router(monitoring_router)
    # Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh)
    # -- `POST /ingestion/refresh/{ticker}`, an explicit, forced
    # provider check; `GET /ingestion/results/{case_id}`, its own
    # read-model cache.
    app.include_router(ingestion_router)
    # Knowledge Orchestration Engine -- `POST /orchestration/{ticker}`,
    # a new, explicit, additive operation (mirrors `POST /ingestion
    # /refresh/{ticker}` exactly): plans and executes only the
    # provider calls current Knowledge Coverage actually justifies,
    # never invoked automatically by any existing trigger.
    app.include_router(knowledge_orchestration_router)
    # Knowledge Strategy Engine -- `GET /research-strategy/{ticker}`, a
    # new, additive, read-only operation: reports every current
    # knowledge gap's Decision Relevance and why, ordered by research
    # priority, without running any provider. `knowledge_orchestration`
    # itself now also consumes this package internally (relevance-based
    # research ordering, a richer Research Completion outcome) -- see
    # `atlas.alpha.knowledge_strategy`'s own module docstring.
    app.include_router(knowledge_strategy_router)
    # Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
    # Understanding) -- `GET /evidence-graph/{case_id}`, the dependency
    # network among one Case's own Observations/Evidence/Decisions/
    # Outcomes/CaseConditions/Assumptions/Findings, plus its weak
    # dependencies.
    app.include_router(evidence_graph_router)
    # Atlas Intelligence Sprint 11 (Decision Readiness & Decision
    # Eligibility) -- `GET /decision-readiness/{case_id}`, whether Atlas
    # has genuinely reached the point where a decision is justified.
    app.include_router(decision_readiness_router)
    # Atlas Decision Layer Sprint 1 (Investment Decision Synthesis) --
    # `GET /investment-decision/{case_id}`, one synthesized Buy/Add/
    # Hold/Reduce/Exit/Wait/No Decision, reused from Decision Support/
    # Decision Readiness/Stance, never a new judgment.
    app.include_router(investment_decision_router)
    # Atlas Decision Layer Sprint 2 (Recommendation Strength &
    # Conviction) -- `GET /recommendation-conviction/{case_id}`, how
    # strongly Atlas stands behind the Investment Decision it already
    # recommended; never a probability, never a new recommendation.
    app.include_router(recommendation_conviction_router)
    # Atlas Decision Layer Sprint 3 (Decision Path & Required
    # Progress) -- `GET /decision-path/{case_id}`, exactly what would
    # need to change before Atlas recommends something different;
    # deterministic dependency analysis, never a forecast.
    app.include_router(decision_path_router)
    # Atlas Decision Layer Sprint 4 (Decision Alternatives &
    # Opportunity Cost) -- `GET /opportunity-cost/{case_id}`, what a
    # decision genuinely competes against (another Case, waiting,
    # cash); deterministic comparison only, never a choice made for
    # the investor.
    app.include_router(opportunity_cost_router)
    # Atlas Decision Layer Sprint 5 (Decision Memory) -- `GET
    # /decision-memory/{case_id}`, the durable, append-only history of
    # every real change to this Case's own decision; never overwrites
    # a prior snapshot.
    app.include_router(decision_memory_router)
    # Atlas Decision Layer Sprint 6 (Decision Explanation &
    # Traceability) -- `GET /decision-explanation/{case_id}`, one
    # coherent, traceable explanation for why Atlas reached this
    # Case's own current decision; computes no new analysis.
    app.include_router(decision_explanation_router)
    # Atlas Decision Layer Sprint 7 (Decision Reliability) -- `GET
    # /decision-reliability/{case_id}`, how trustworthy this Case's
    # own decision is, reclassified from Coverage/Confidence, Evidence
    # Quality, and Decision Readiness; computes no new analysis.
    app.include_router(decision_reliability_router)
    # Atlas Decision Layer Sprint 8 (Portfolio Decision Synthesis) --
    # `GET /portfolio-decision/{case_id}`, what this Case's own
    # decision means for the investor's actual portfolio -- capital
    # competition, portfolio context, and a real conflict/support
    # classification; computes no new portfolio analysis.
    app.include_router(portfolio_decision_router)
    register_case_error_handlers(app)
    register_decision_error_handlers(app)
    register_security_confirmation_error_handlers(app)
    register_security_identity_evidence_error_handlers(app)
    register_decision_context_error_handlers(app)
    register_decision_draft_error_handlers(app)
    register_case_condition_error_handlers(app)
    register_assumption_error_handlers(app)
    register_observation_error_handlers(app)
    register_hypothesis_error_handlers(app)
    register_evidence_error_handlers(app)
    register_knowledge_reference_error_handlers(app)
    register_judgment_error_handlers(app)
    register_reasoning_trace_error_handlers(app)
    register_outcome_error_handlers(app)
    return app


app = create_app()
