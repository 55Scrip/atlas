"""Orchestration for the Daily Brief Agenda -- the only part of this
package that performs I/O. Composes seven existing services, every one
unmodified: `atlas.alpha.daily_brief.DailyBriefService` (Change
Intelligence), `atlas.alpha.portfolio_fit.PortfolioFitService`
(Portfolio Fit), `atlas.alpha.portfolio_status.PortfolioStatusService`
(workflow items), `atlas.alpha.portfolio_intelligence
.PortfolioIntelligenceService` (portfolio-wide findings), the
Reasoning Workspace's own `list_active_case_conditions`/
`list_active_assumptions` read models (Case Condition / Assumption
state), and (Atlas Intelligence Sprint 7) `atlas.alpha.monitoring
.MonitoringService`'s own read model (Coverage/Confidence/Stance/
Evidence Quality/Evidence Timeline change detection). See this
package's own `__init__.py` for the full rationale.

**Monitoring is read here, never run here.** `build_agenda()` reads
`MonitoringService.read_model()` -- the last explicit `POST
/monitoring/run`'s own cached output -- never `.run()` itself. Calling
`.run()` from a Daily Brief page load would silently turn a read
endpoint into a second, heavier, undisclosed trigger for exactly the
per-Case recompute-and-capture sequence Deliverable 19's own audit
found already happens on too many independent read paths; it would
also contradict Deliverable 20's own "not a scheduler" instruction by
making every Daily Brief view an implicit one. If no monitoring run has
ever happened, the read model is simply empty, and Monitoring
contributes no signals this call -- an honest absence, not an error.

**Known, disclosed cost: each of these composes `InvestmentCase
CompositionService.build(case_id)` independently for the same Case.**
`DailyBriefService` and `PortfolioFitService` each already call it once
per Case for their own purpose; this service does not attempt to merge
those two composition passes into one, because doing so would mean
reaching into either service's own internals -- itself a violation of
"reuse existing engines exactly as they are." This is a real, accepted
I/O cost (several redundant `InvestmentCaseComposition` builds per
Case), not a correctness or duplicated-logic concern -- see the Final
Report's own "Product limitations remaining" for this exact tradeoff.

**Performance Sprint 1 (Daily Brief Optimization).** Profiling confirmed
the above "known, disclosed cost" was far larger than disclosed:
`InvestmentCaseCompositionService.build()` was measured at 5,607 calls
for only 9 distinct Cases in one `build_agenda()` run -- every signal
source above, plus nested cross-Case comparisons inside `opportunity_
cost`/`decision_memory`/`portfolio_decision`, each independently
rebuilding the identical, deterministic `InvestmentCaseComposition` for
a Case already built moments earlier in the same call. `build_agenda()`
now memoizes `composition_service.build` for the duration of exactly
this one call, via a temporary wrapper installed at the start and
removed in a `finally` block at the end (see `build_agenda`'s own
comment). This is deliberately NOT a change to
`InvestmentCaseCompositionService` itself -- an earlier version of this
fix added the cache directly to that class and broke three existing
tests that legitimately reuse one `InvestmentCaseCompositionService`
instance across a build -> mutate -> build sequence to verify change
detection (a real, valid pattern outside the request-scoped HTTP path).
Scoping the cache to exactly one `build_agenda()` call, installed and
torn down around it, gets the identical performance win with zero
observable effect on `composition_service` for any other caller,
before or after this call, including that class's own test suite.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from atlas.alpha.case_membership import known_cases
from atlas.alpha.daily_brief.service import DailyBriefService
from atlas.alpha.daily_brief_agenda.engine import (
    Signal,
    TickerContext,
    assumption_signal,
    build_agenda,
    business_quality_signal,
    case_condition_signal,
    change_intelligence_signal,
    concentration_signal,
    decision_explanation_signal,
    decision_reliability_signal,
    executive_change_signal,
    management_credibility_signal,
    portfolio_decision_signal,
    decision_memory_signal,
    decision_readiness_signal,
    evidence_gap_signal,
    decision_path_signal,
    investment_decision_signal,
    monitoring_signal,
    opportunity_cost_signal,
    portfolio_fit_signal,
    portfolio_level_signal,
    recommendation_conviction_signal,
    workflow_signal,
)
from atlas.alpha.daily_brief_agenda.models import DailyBriefAgenda, PriorityLevel
from atlas.alpha.daily_brief_agenda.reason_facts import ReasonCode, ReasonFact
from atlas.alpha.decision_explanation.models import DecisionExplanationChange
from atlas.alpha.decision_explanation.service import DecisionExplanationService
from atlas.alpha.decision_reliability.models import ReliabilityChange
from atlas.alpha.decision_reliability.service import DecisionReliabilityService
from atlas.alpha.portfolio_decision.models import PortfolioDecisionChange
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService
from atlas.alpha.decision_memory.models import DecisionMemoryChange
from atlas.alpha.decision_memory.service import DecisionMemoryService
from atlas.alpha.decision_path.models import DecisionPathChange
from atlas.alpha.decision_path.service import DecisionPathService
from atlas.alpha.decision_readiness.models import DecisionReadiness, DecisionReadinessChange, DecisionReadinessStatus
from atlas.alpha.decision_readiness.service import DecisionReadinessService
from atlas.alpha.evidence_graph.service import EvidenceGraphService
from atlas.alpha.opportunity_cost.models import OpportunityCostChange
from atlas.alpha.opportunity_cost.service import OpportunityCostService
from atlas.alpha.investment_case.models import InvestmentCaseComposition
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.investment_case.executive_change_intelligence import LeadershipChangeEvent
from atlas.alpha.investment_case.management_credibility_intelligence import CredibilityFindingKind
from atlas.alpha.investment_decision.models import DecisionAction, DecisionChange, InvestmentDecision
from atlas.alpha.investment_decision.service import InvestmentDecisionService
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio_fit.service import PortfolioFitService
from atlas.alpha.portfolio_intelligence.models import KeyFindingKind
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService
from atlas.alpha.portfolio_status.models import AttentionCategory
from atlas.alpha.portfolio_status.service import PortfolioStatusService
from atlas.alpha.recommendation_conviction.models import ConvictionChange, ConvictionStrength
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.core.application.assumption.assumption_service import AssumptionService
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.application.reasoning_workspace.read_models import (
    list_active_assumptions,
    list_active_case_conditions,
)
from atlas.core.domain.case.value_objects import CaseId

__all__ = ["DailyBriefAgendaService"]

_Bundles = dict[str, tuple[TickerContext, list[Signal]]]

_READINESS_STATUS_LABEL: dict[DecisionReadinessStatus, str] = {
    DecisionReadinessStatus.READY: "ready",
    DecisionReadinessStatus.ALMOST_READY: "almost ready",
    DecisionReadinessStatus.WAITING: "waiting",
    DecisionReadinessStatus.BLOCKED: "blocked",
    DecisionReadinessStatus.UNAVAILABLE: "not yet evaluated",
    DecisionReadinessStatus.UNKNOWN: "unknown",
}
"""Fixed English text, the same "not translated per-user-language"
choice Change Intelligence's own `thesis_impact_sentence` already
makes for Daily Brief reason strings (see `DailyBriefEntry`'s own
docstring)."""


def _decision_readiness_change_reason(ticker: str, change: DecisionReadinessChange) -> str:
    """Deliverable 10 -- "what changed. why readiness changed. which
    evidence caused it," in one fixed-vocabulary sentence: the status
    transition itself, plus every blocker that was resolved or newly
    introduced -- each blocker kind name *is* the real evidence
    category (e.g. "conflicting evidence"), never a generic label."""
    sentence = (
        f"{ticker}: Decision readiness changed from {_READINESS_STATUS_LABEL[change.previous_status]} "
        f"to {_READINESS_STATUS_LABEL[change.current_status]}."
    )
    if change.resolved_blockers:
        resolved = ", ".join(kind.value.replace("_", " ") for kind in change.resolved_blockers)
        sentence += f" Resolved: {resolved}."
    if change.new_blockers:
        new = ", ".join(kind.value.replace("_", " ") for kind in change.new_blockers)
        sentence += f" New: {new}."
    return sentence


_ACTION_LABEL: dict[DecisionAction, str] = {
    DecisionAction.BUY: "buy",
    DecisionAction.ADD: "add",
    DecisionAction.HOLD: "hold",
    DecisionAction.REDUCE: "reduce",
    DecisionAction.EXIT: "exit",
    DecisionAction.WAIT: "wait",
    DecisionAction.NO_DECISION: "no decision",
}
"""Fixed English text, the same "not translated per-user-language"
choice `_READINESS_STATUS_LABEL` above already makes."""


def _investment_decision_change_reason(ticker: str, change: DecisionChange) -> str:
    """Deliverable 10 -- "changed from Hold to Add, became blocked,
    became actionable" in one fixed-vocabulary sentence: the action
    transition itself, plus which qualifiers were gained or lost."""
    sentence = (
        f"{ticker}: Investment decision changed from {_ACTION_LABEL[change.previous_action]} "
        f"to {_ACTION_LABEL[change.current_action]}."
    )
    gained = set(change.current_qualifier_kinds) - set(change.previous_qualifier_kinds)
    lost = set(change.previous_qualifier_kinds) - set(change.current_qualifier_kinds)
    if gained:
        gained_text = ", ".join(sorted(kind.value.replace("_", " ") for kind in gained))
        sentence += f" New: {gained_text}."
    if lost:
        lost_text = ", ".join(sorted(kind.value.replace("_", " ") for kind in lost))
        sentence += f" Resolved: {lost_text}."
    return sentence


_STRENGTH_LABEL: dict[ConvictionStrength, str] = {
    ConvictionStrength.VERY_STRONG: "very strong",
    ConvictionStrength.STRONG: "strong",
    ConvictionStrength.MODERATE: "moderate",
    ConvictionStrength.WEAK: "weak",
    ConvictionStrength.VERY_WEAK: "very weak",
    ConvictionStrength.UNAVAILABLE: "not available",
}
"""Fixed English text, the same "not translated per-user-language"
choice `_READINESS_STATUS_LABEL`/`_ACTION_LABEL` above already make."""


def _recommendation_conviction_change_reason(ticker: str, change: ConvictionChange) -> str:
    """Deliverable 10 -- "conviction improved/reduced, operational
    blocker removed, evidence strengthened" in one fixed-vocabulary
    sentence: the strength transition itself, the stability transition
    when it also moved, and which specific reasons were gained/lost."""
    sentence = f"{ticker}: Recommendation conviction changed from {_STRENGTH_LABEL[change.previous_strength]} to {_STRENGTH_LABEL[change.current_strength]}."
    if change.previous_stability != change.current_stability:
        sentence += f" Stability changed from {change.previous_stability.value.replace('_', ' ')} to {change.current_stability.value.replace('_', ' ')}."
    if change.new_limiting_reasons:
        new_text = ", ".join(sorted(r.code.replace("_", " ") for r in change.new_limiting_reasons))
        sentence += f" New: {new_text}."
    if change.resolved_limiting_reasons:
        resolved_text = ", ".join(sorted(r.code.replace("_", " ") for r in change.resolved_limiting_reasons))
        sentence += f" Resolved: {resolved_text}."
    return sentence


_FINAL_REACHABLE_STATE_LABEL: dict = {
    "already_reached": "nothing holding it back",
    "fully_reachable": "every remaining step has a real path forward",
    "partially_reachable": "some progress possible, one step has no path today",
    "not_reachable": "no path forward today",
}
"""Fixed English text, the same "not translated per-user-language"
choice every prior label dict in this module already makes."""


def _decision_path_change_reason(ticker: str, change: DecisionPathChange) -> str:
    """Deliverable 10 -- "decision path shortened/blocked, operational
    blocker removed, evidence blocker resolved, dependency resolved"
    in one fixed-vocabulary sentence: the endpoint transition itself,
    plus which specific dependencies were gained or lost."""
    sentence = (
        f"{ticker}: Decision path changed from {_FINAL_REACHABLE_STATE_LABEL[change.previous_final_reachable_state.value]} "
        f"to {_FINAL_REACHABLE_STATE_LABEL[change.current_final_reachable_state.value]}."
    )
    if change.resolved_steps:
        resolved_text = ", ".join(sorted(s.dependency.code.replace("_", " ") for s in change.resolved_steps))
        sentence += f" Resolved: {resolved_text}."
    if change.new_steps:
        new_text = ", ".join(sorted(s.dependency.code.replace("_", " ") for s in change.new_steps))
        sentence += f" New: {new_text}."
    return sentence


def _alternative_label(alternative) -> str:
    return alternative.ticker if alternative.ticker is not None else alternative.kind.value.replace("_", " ")


def _opportunity_cost_change_reason(ticker: str, change: OpportunityCostChange) -> str:
    """Deliverable 10 -- "new alternative became available. alternative
    disappeared. alternative strengthened. alternative weakened.
    waiting became preferable. alternative comparison changed" in one
    fixed-vocabulary sentence naming each real alternative that
    changed."""
    parts: list[str] = []
    if change.new_alternatives:
        parts.append("New: " + ", ".join(sorted(_alternative_label(a) for a in change.new_alternatives)) + ".")
    if change.disappeared_alternatives:
        parts.append("No longer available: " + ", ".join(sorted(_alternative_label(a) for a in change.disappeared_alternatives)) + ".")
    if change.strengthened_alternatives:
        parts.append("Strengthened: " + ", ".join(sorted(_alternative_label(a) for a in change.strengthened_alternatives)) + ".")
    if change.weakened_alternatives:
        parts.append("Weakened: " + ", ".join(sorted(_alternative_label(a) for a in change.weakened_alternatives)) + ".")
    if change.primary_alternative_changed:
        parts.append("The primary alternative changed.")
    detail = " ".join(parts) if parts else "The alternatives for this decision changed."
    return f"{ticker}: {detail}"


_CHANGE_DIRECTION_LABEL: dict = {
    "stronger": "strengthened",
    "weaker": "weakened",
    "unchanged": "unchanged",
}
"""Fixed English text, the same "not translated per-user-language"
choice every prior label dict in this module already makes."""


def _decision_memory_change_reason(ticker: str, change: DecisionMemoryChange) -> str:
    """Deliverable 10 -- "recommendation changed, conviction/readiness/
    decision path direction, blockers resolved/added, alternatives
    changed" in one fixed-vocabulary sentence naming each structured
    field that actually changed. Never free text, never a summary of
    what Atlas "learned" -- every clause below reads directly off a
    `DecisionMemoryChange` field, nothing inferred."""
    parts: list[str] = []
    if change.recommendation_changed:
        previous = change.previous_action.value.replace("_", " ") if change.previous_action is not None else "unknown"
        current = change.current_action.value.replace("_", " ")
        parts.append(f"Recommendation changed from {previous} to {current}.")
    if change.conviction_direction is not None and change.conviction_direction.value != "unchanged":
        parts.append(f"Conviction {_CHANGE_DIRECTION_LABEL[change.conviction_direction.value]}.")
    if change.readiness_direction is not None and change.readiness_direction.value != "unchanged":
        parts.append(f"Readiness {_CHANGE_DIRECTION_LABEL[change.readiness_direction.value]}.")
    if change.decision_path_direction is not None and change.decision_path_direction.value != "unchanged":
        parts.append(f"Decision path {_CHANGE_DIRECTION_LABEL[change.decision_path_direction.value]}.")
    if change.blockers_resolved:
        parts.append("Resolved: " + ", ".join(sorted(c.replace("_", " ") for c in change.blockers_resolved)) + ".")
    if change.blockers_added:
        parts.append("New: " + ", ".join(sorted(c.replace("_", " ") for c in change.blockers_added)) + ".")
    if change.alternative_changed:
        parts.append("The alternatives for this decision changed.")
    detail = " ".join(parts) if parts else "The recorded decision changed."
    return f"{ticker}: {detail}"


def _decision_explanation_change_reason(ticker: str, change: DecisionExplanationChange) -> str:
    """Deliverable 10 -- "explanation changed, new supporting finding,
    resolved blocker, supporting evidence expanded" in one fixed-
    vocabulary sentence naming each structured field that actually
    changed. Every clause reads directly off a `DecisionExplanationChange`
    field, nothing inferred; every reference id named below is a real,
    already-real code/id, never anonymous."""
    parts: list[str] = []
    if change.new_supporting:
        parts.append("New support: " + ", ".join(sorted(sf.reference.id.replace("_", " ") for sf in change.new_supporting)) + ".")
    if change.resolved_blocking:
        parts.append(
            "Resolved: " + ", ".join(sorted(bf.reference.id.replace("_", " ") for bf in change.resolved_blocking)) + "."
        )
    if change.new_blocking:
        parts.append("New: " + ", ".join(sorted(bf.reference.id.replace("_", " ") for bf in change.new_blocking)) + ".")
    if change.evidence_expanded:
        parts.append("Supporting evidence expanded.")
    if change.conviction_direction is not None and change.conviction_direction.value != "unchanged":
        parts.append(f"Conviction {_CHANGE_DIRECTION_LABEL[change.conviction_direction.value]}.")
    detail = " ".join(parts) if parts else "The explanation for this decision changed."
    return f"{ticker}: {detail}"


def _decision_reliability_change_reason(ticker: str, change: ReliabilityChange) -> str:
    """Deliverable 11 -- "reliability improved/weakened, operational
    issue resolved, evidence strengthened" in one fixed-vocabulary
    sentence naming each structured field that actually changed. Every
    clause reads directly off a `ReliabilityChange` field, nothing
    inferred."""
    parts: list[str] = []
    if change.previous_level != change.current_level:
        parts.append(f"Reliability changed from {change.previous_level.value} to {change.current_level.value}.")
    if change.resolved_limiting:
        parts.append(
            "Resolved: " + ", ".join(sorted(r.reference.id.replace("_", " ") for r in change.resolved_limiting)) + "."
        )
    if change.new_limiting:
        parts.append("New: " + ", ".join(sorted(r.reference.id.replace("_", " ") for r in change.new_limiting)) + ".")
    detail = " ".join(parts) if parts else "The reliability of this decision changed."
    return f"{ticker}: {detail}"


def _portfolio_decision_change_reason(ticker: str, change: PortfolioDecisionChange) -> str:
    """Deliverable 11 -- "portfolio decision changed, capital
    competition changed, portfolio conflict resolved, portfolio
    opportunity appeared" in one fixed-vocabulary sentence naming each
    structured field that actually changed. Every clause reads
    directly off a `PortfolioDecisionChange` field, nothing inferred."""
    parts: list[str] = []
    if change.previous_category != change.current_category:
        parts.append(f"Portfolio decision changed from {change.previous_category.value} to {change.current_category.value}.")
    if change.competition_changed:
        parts.append("Capital competition changed.")
    if change.resolved_limiting:
        parts.append(
            "Resolved: " + ", ".join(sorted(r.reference.id.replace("_", " ") for r in change.resolved_limiting)) + "."
        )
    if change.new_limiting:
        parts.append("New: " + ", ".join(sorted(r.reference.id.replace("_", " ") for r in change.new_limiting)) + ".")
    detail = " ".join(parts) if parts else "What this decision means for the portfolio changed."
    return f"{ticker}: {detail}"


_LEADERSHIP_EVENT_LABEL: dict[str, str] = {
    "appointment": "appointed", "departure": "departed", "resignation": "resigned",
    "retirement": "retired", "termination": "was terminated", "promotion": "was promoted",
    "interim_appointment": "appointed on an interim basis", "permanent_appointment": "appointed on a permanent basis",
    "board_appointment": "appointed to the board", "board_departure": "departed the board", "role_change": "changed role",
}


def _executive_change_reason(ticker: str, event: LeadershipChangeEvent) -> str:
    """Product Intelligence Sprint 1. Fixed English text, the same
    "not translated per-user-language" precedent every other reason
    string in this file already follows -- reads directly off a real
    `LeadershipChangeEvent`, nothing inferred."""
    verb = _LEADERSHIP_EVENT_LABEL.get(event.event_type.value, "changed role")
    return f"{ticker}: {event.executive_name} ({event.role_category.value.upper()}) {verb}."


def _management_credibility_reason(ticker: str, kind: CredibilityFindingKind) -> str:
    if kind is CredibilityFindingKind.INCONSISTENT_FOLLOW_THROUGH:
        return f"{ticker}: Management's own prior commitments were not fulfilled."
    return f"{ticker}: Guidance was revised downward."


def _business_quality_reason(ticker: str) -> str:
    return f"{ticker}: Business fundamentals are weakening."


class DailyBriefAgendaService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        daily_brief_service: DailyBriefService,
        portfolio_fit_service: PortfolioFitService,
        portfolio_status_service: PortfolioStatusService,
        portfolio_intelligence_service: PortfolioIntelligenceService,
        case_condition_service: CaseConditionService,
        assumption_service: AssumptionService,
        monitoring_service: MonitoringService,
        evidence_graph_service: EvidenceGraphService,
        decision_readiness_service: DecisionReadinessService,
        investment_decision_service: InvestmentDecisionService,
        recommendation_conviction_service: RecommendationConvictionService,
        decision_path_service: DecisionPathService,
        opportunity_cost_service: OpportunityCostService,
        decision_memory_service: DecisionMemoryService,
        decision_explanation_service: DecisionExplanationService,
        decision_reliability_service: DecisionReliabilityService,
        portfolio_decision_service: PortfolioDecisionService,
        composition_service: InvestmentCaseCompositionService,
    ) -> None:
        self._composition_service = composition_service
        self._evidence_graph_service = evidence_graph_service
        self._decision_readiness_service = decision_readiness_service
        self._investment_decision_service = investment_decision_service
        self._recommendation_conviction_service = recommendation_conviction_service
        self._decision_path_service = decision_path_service
        self._opportunity_cost_service = opportunity_cost_service
        self._decision_memory_service = decision_memory_service
        self._decision_explanation_service = decision_explanation_service
        self._decision_reliability_service = decision_reliability_service
        self._portfolio_decision_service = portfolio_decision_service
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._daily_brief_service = daily_brief_service
        self._portfolio_fit_service = portfolio_fit_service
        self._portfolio_status_service = portfolio_status_service
        self._portfolio_intelligence_service = portfolio_intelligence_service
        self._case_condition_service = case_condition_service
        self._assumption_service = assumption_service
        self._monitoring_service = monitoring_service

    def _ensure(self, bundles: _Bundles, ticker: str, case_id: str, is_holding: bool) -> list[Signal]:
        existing = bundles.get(ticker)
        if existing is not None:
            return existing[1]
        signals: list[Signal] = []
        bundles[ticker] = (TickerContext(ticker=ticker, case_id=case_id, is_holding=is_holding, portfolio_context=None), signals)
        return signals

    def build_agenda(self) -> DailyBriefAgenda:
        """Performance Sprint 1: installs a per-call memoization cache
        over `self._composition_service.build` -- shared by every one of
        the 16 signal sources below, directly or through a sub-service
        that itself calls `composition_service.build(case_id)` -- for
        exactly the duration of `_build_agenda_impl()`, then removes it
        in `finally` regardless of success or exception. `build` itself
        is not touched: this shadows it with an instance attribute (the
        normal Python mechanism for overriding one bound method on one
        object) and deletes that attribute afterward, restoring the
        class's own method for every future caller, including a test
        that reuses the same `InvestmentCaseCompositionService` instance
        for something else entirely.

        Performance Sprint 2: the identical technique, extended to
        `decision_readiness_service.assess_for_case` and
        `investment_decision_service.synthesize_for_case`. Profiling
        found these called 855 and 585 times respectively for only 9
        known Cases in one request -- source 8/9 below each already
        call `change_for_case` for every Case exactly once (confirmed
        via `pstats.print_callers`: nothing else ever calls
        `change_for_case`), and *that* first call is what every other
        caller's plain `assess_for_case`/`synthesize_for_case` call
        redundantly repeats moments later, directly or through a chain
        of sibling services that all resolve to these exact same two
        shared instances (every one of their own FastAPI providers
        depends on `Depends(get_decision_readiness_service)` /
        `Depends(get_investment_decision_service)`, the identical
        functions used here -- confirmed by grep, not assumed).
        Cache keys include `ticker` (not just `case_id`): the returned
        value never depends on it, but some callers pass a real ticker
        and others omit it, and preserving exactly which combination
        last reaches the repository's own `upsert` keeps this
        optimization from changing anything persisted, not only what
        this endpoint returns. See this method's own two wrapper
        blocks below for why deduplication is safe here specifically:
        `change_for_case`'s "read the previous result before this
        call's own fresh computation overwrites it" ordering is
        preserved exactly, because sources 8 and 9 always run -- and
        so always populate these caches -- before any other signal
        source (10-16) or nested sub-service call ever asks for the
        same Case.

        Performance Sprint 1 (re-run) -- profiling against the current
        codebase found the identical pattern one layer further down the
        Decision Layer's own dependency graph: `evidence_graph_service
        .build_for_case` (243 calls for 9 real Cases -- 27x), `recommen
        dation_conviction_service.assess_for_case` (144 calls -- 16x,
        `opportunity_cost_service._other_case_summaries` alone calls it
        once per *other* known Case for every Case it assesses),
        `decision_path_service.build_for_case` (72 calls -- 8x), and
        `opportunity_cost_service.assess_for_case` (36 calls -- 4x),
        each confirmed via `pstats.print_callers` to be a pure read
        (`evidence_graph_service.build_for_case` persists nothing at
        all) or the identical "compute, then idempotently upsert the
        same deterministic result" shape already established safe
        above -- `change_for_case` remains untouched on all three, so
        its own "read previous, then compute fresh" ordering is
        preserved exactly. Source 10 (Recommendation Conviction), 11
        (Decision Path), and source 1's own direct `evidence_graph
        _service.build_for_case` call already run before any nested
        caller (`_build_inputs` chains inside Decision Path/Opportunity
        Cost/Decision Memory/Decision Explanation) ever asks for the
        same Case -- confirmed by this module's own source ordering,
        not assumed -- so the same "first real call populates the
        cache" precondition Sprint 2 already relies on holds here too."""
        cache: dict[str, InvestmentCaseComposition | None] = {}
        original_build = self._composition_service.build

        def _cached_build(case_id_str: str) -> InvestmentCaseComposition | None:
            if case_id_str in cache:
                return cache[case_id_str]
            result = original_build(case_id_str)
            cache[case_id_str] = result
            return result

        self._composition_service.build = _cached_build  # type: ignore[method-assign]

        readiness_cache: dict[tuple[str, str | None], DecisionReadiness | None] = {}
        original_assess_readiness = self._decision_readiness_service.assess_for_case

        def _cached_assess_readiness(case_id: str, *, ticker: str | None = None) -> DecisionReadiness | None:
            key = (case_id, ticker)
            if key in readiness_cache:
                return readiness_cache[key]
            result = original_assess_readiness(case_id, ticker=ticker)
            readiness_cache[key] = result
            return result

        self._decision_readiness_service.assess_for_case = _cached_assess_readiness  # type: ignore[method-assign]

        decision_cache: dict[tuple[str, str | None], InvestmentDecision | None] = {}
        original_synthesize_decision = self._investment_decision_service.synthesize_for_case

        def _cached_synthesize_decision(case_id: str, *, ticker: str | None = None) -> InvestmentDecision | None:
            key = (case_id, ticker)
            if key in decision_cache:
                return decision_cache[key]
            result = original_synthesize_decision(case_id, ticker=ticker)
            decision_cache[key] = result
            return result

        self._investment_decision_service.synthesize_for_case = _cached_synthesize_decision  # type: ignore[method-assign]

        evidence_graph_cache: dict[str, object] = {}
        original_build_evidence_graph = self._evidence_graph_service.build_for_case

        def _cached_build_evidence_graph(case_id_str: str):
            if case_id_str in evidence_graph_cache:
                return evidence_graph_cache[case_id_str]
            result = original_build_evidence_graph(case_id_str)
            evidence_graph_cache[case_id_str] = result
            return result

        self._evidence_graph_service.build_for_case = _cached_build_evidence_graph  # type: ignore[method-assign]

        conviction_cache: dict[tuple[str, str | None], object] = {}
        original_assess_conviction = self._recommendation_conviction_service.assess_for_case

        def _cached_assess_conviction(case_id: str, *, ticker: str | None = None):
            key = (case_id, ticker)
            if key in conviction_cache:
                return conviction_cache[key]
            result = original_assess_conviction(case_id, ticker=ticker)
            conviction_cache[key] = result
            return result

        self._recommendation_conviction_service.assess_for_case = _cached_assess_conviction  # type: ignore[method-assign]

        decision_path_cache: dict[tuple[str, str | None], object] = {}
        original_build_decision_path = self._decision_path_service.build_for_case

        def _cached_build_decision_path(case_id: str, *, ticker: str | None = None):
            key = (case_id, ticker)
            if key in decision_path_cache:
                return decision_path_cache[key]
            result = original_build_decision_path(case_id, ticker=ticker)
            decision_path_cache[key] = result
            return result

        self._decision_path_service.build_for_case = _cached_build_decision_path  # type: ignore[method-assign]

        opportunity_cost_cache: dict[tuple[str, str | None], object] = {}
        original_assess_opportunity_cost = self._opportunity_cost_service.assess_for_case

        def _cached_assess_opportunity_cost(case_id: str, *, ticker: str | None = None):
            key = (case_id, ticker)
            if key in opportunity_cost_cache:
                return opportunity_cost_cache[key]
            result = original_assess_opportunity_cost(case_id, ticker=ticker)
            opportunity_cost_cache[key] = result
            return result

        self._opportunity_cost_service.assess_for_case = _cached_assess_opportunity_cost  # type: ignore[method-assign]

        try:
            return self._build_agenda_impl()
        finally:
            del self._composition_service.build
            del self._decision_readiness_service.assess_for_case
            del self._investment_decision_service.synthesize_for_case
            del self._evidence_graph_service.build_for_case
            del self._recommendation_conviction_service.assess_for_case
            del self._decision_path_service.build_for_case
            del self._opportunity_cost_service.assess_for_case

    def _build_agenda_impl(self) -> DailyBriefAgenda:
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()
        bundles: _Bundles = {}
        # The one authoritative ticker->caseId map (Portfolio takes
        # precedence, mirroring `known_cases`'s own dedup) -- every
        # signal source below that only has a ticker in hand (the
        # concentration finding) resolves its real Case ID from here,
        # rather than fabricating one.
        known = known_cases(self._portfolio_store, self._watchlist_store)
        ticker_to_case_id = {ticker: case_id for case_id, ticker in known if ticker is not None}

        # 1. Change Intelligence -- `DailyBriefService.build_daily_brief()`
        # unmodified; already filters to real, non-baseline changes only.
        brief = self._daily_brief_service.build_daily_brief()
        for entry in brief.entries:
            ticker = entry.ticker or entry.case_id
            is_holding = entry.ticker in held_tickers if entry.ticker else False
            reason = f"{ticker}: {entry.why_it_matters}"
            # Atlas Intelligence Sprint 10 (Evidence Graph & Dependency
            # Understanding, Deliverable 10) -- "detta påverkar tre
            # slutsatser." The single most-connected real change for
            # this Case, never summed across changes (summing risks
            # double-counting a Finding two changes both point at).
            built = self._evidence_graph_service.build_for_case(entry.case_id)
            affected_finding_count = max(
                (i.affected_finding_count for i in built.impacted_changes), default=0
            ) if built is not None else 0
            self._ensure(bundles, ticker, entry.case_id, is_holding).append(
                change_intelligence_signal(entry.thesis_impact, reason, affected_finding_count=affected_finding_count)
            )

        # 2. Portfolio Fit -- `PortfolioFitService` unmodified, both its
        # existing public methods (holdings + candidates already exclude
        # each other, see that service's own docstring).
        for assessment in self._portfolio_fit_service.assess_all_holdings():
            reason_text = assessment.overall_reasoning[0] if assessment.overall_reasoning else f"Portfolio Fit is {assessment.overall.value}"
            signal = portfolio_fit_signal(assessment.overall, assessment.trend, True, f"{assessment.ticker}: {reason_text}")
            if signal is not None:
                self._ensure(bundles, assessment.ticker, assessment.case_id, True).append(signal)
        for assessment in self._portfolio_fit_service.rank_candidates():
            reason_text = assessment.overall_reasoning[0] if assessment.overall_reasoning else f"Portfolio Fit is {assessment.overall.value}"
            signal = portfolio_fit_signal(assessment.overall, assessment.trend, False, f"{assessment.ticker}: {reason_text}")
            if signal is not None:
                self._ensure(bundles, assessment.ticker, assessment.case_id, False).append(signal)

        # 3. Case Condition / Assumption -- loop every known Case
        # (Portfolio + Watchlist), the same per-Case loop `atlas.alpha
        # .daily_brief`/`atlas.alpha.portfolio_fit` already use for the
        # identical "must cover both" reason.
        for case_id_str, ticker in known:
            resolved_ticker = ticker or case_id_str
            is_holding = ticker in held_tickers if ticker else False
            case_id = CaseId(value=uuid.UUID(case_id_str))
            for row in list_active_case_conditions(self._case_condition_service, case_id):
                predicate = row.predicate_text or "CaseCondition"
                reason = f"{resolved_ticker}: {predicate} ({row.status})"
                # `label` is the investor's own predicate text -- real
                # free text, never translated (see `reason_facts.py`'s
                # own docstring). When it's absent, there is nothing
                # honest to translate: leave `fact` unset so the
                # frontend falls back to the raw `reason` text above,
                # the same "structured field present -> use it; absent
                # -> fall back" contract every other converted source
                # here already follows.
                fact = (
                    ReasonFact(ReasonCode.CASE_CONDITION_STATUS, resolved_ticker, value=row.status, label=row.predicate_text)
                    if row.predicate_text
                    else None
                )
                signal = case_condition_signal(row.role or "monitoring", row.status, reason, row.updated_at, fact=fact)
                if signal is not None:
                    self._ensure(bundles, resolved_ticker, case_id_str, is_holding).append(signal)
            for row in list_active_assumptions(self._assumption_service, case_id):
                statement = row.statement or "Assumption"
                reason = f"{resolved_ticker}: {statement} ({row.status})"
                fact = (
                    ReasonFact(ReasonCode.ASSUMPTION_STATUS, resolved_ticker, value=row.status, label=row.statement)
                    if row.statement
                    else None
                )
                signal = assumption_signal(row.status, reason, row.updated_at, fact=fact)
                if signal is not None:
                    self._ensure(bundles, resolved_ticker, case_id_str, is_holding).append(signal)

        # 4. Workflow items -- `PortfolioStatusService` unmodified,
        # ported verbatim from `derivePortfolioActions.ts`'s own
        # `reviewQueue`-is-primary-source reading (see `engine.py`).
        status_report = self._portfolio_status_service.build_report()
        for item in status_report.review_queue:
            if item.case_id is None:
                continue
            reason = f"{item.ticker}: {item.top_category.value.replace('_', ' ').lower()} ({item.reason_count} item(s))"
            fact = ReasonFact(ReasonCode.WORKFLOW_GAP, item.ticker, value=item.top_category.value, count=item.reason_count)
            signal = workflow_signal(item.top_category, reason, count=item.reason_count, fact=fact)
            self._ensure(bundles, item.ticker, item.case_id, True).append(signal)

        # 5. Portfolio-wide findings -- `PortfolioIntelligenceService`
        # unmodified. `HIGH_CONCENTRATION`/`ELEVATED_CONCENTRATION` name
        # a real ticker (their own largest-position driver) and become a
        # per-ticker signal; `LARGE_UNALLOCATED` has none and becomes a
        # portfolio-level item. The other three `KeyFindingKind` members
        # are aggregate statistics already represented by the per-ticker
        # signals above (mirrors `derivePortfolioActions.ts`'s own
        # identical omission, same reasoning).
        intelligence_report = self._portfolio_intelligence_service.build_report()
        portfolio_level_signals: list[Signal] = []
        for finding in intelligence_report.key_findings:
            if finding.kind in (KeyFindingKind.HIGH_CONCENTRATION, KeyFindingKind.ELEVATED_CONCENTRATION) and finding.tickers:
                ticker = finding.tickers[0]
                case_id_for_ticker = ticker_to_case_id.get(ticker)
                if case_id_for_ticker is None:
                    continue
                reason = f"{ticker}: {finding.kind.value.replace('_', ' ')}"
                fact = ReasonFact(ReasonCode.CONCENTRATION, ticker, value=finding.kind.value)
                signal = concentration_signal(finding.kind, reason, fact=fact)
                if signal is not None:
                    self._ensure(bundles, ticker, case_id_for_ticker, ticker in held_tickers).append(signal)
            elif finding.kind is KeyFindingKind.LARGE_UNALLOCATED:
                reason = f"Large unallocated capital across {finding.count} consideration(s)"
                fact = ReasonFact(ReasonCode.LARGE_UNALLOCATED_CAPITAL, "portfolio", count=finding.count)
                portfolio_level_signals.append(portfolio_level_signal(PriorityLevel.NORMAL, reason, fact=fact))

        # 6. Missing evidence -- `PortfolioIntelligenceReport.missing_evidence`,
        # the one "Needs Your Attention" (`derivePortfolioActions.ts`)
        # signal this engine previously had no equivalent for (Sprint 8,
        # Deliverable 4). Same `intelligence_report` already fetched
        # above; every holding's evidence gap becomes a real, portfolio-
        # group item -- `missing_evidence` is portfolio-only (Case
        # Evaluation only runs for real holdings), so `is_holding=True`
        # always, mirroring workflow items above.
        for gap in intelligence_report.missing_evidence:
            reason = f"{gap.ticker}: missing evidence ({gap.gap_kind.value.replace('_', ' ')})"
            fact = ReasonFact(ReasonCode.MISSING_EVIDENCE, gap.ticker, value=gap.gap_kind.value)
            self._ensure(bundles, gap.ticker, gap.case_id, True).append(evidence_gap_signal(reason, fact=fact))

        # 7. Monitoring & Change Detection (Atlas Intelligence Sprint 7,
        # Deliverable 10) -- reads the last `POST /monitoring/run`'s own
        # cached read model, never recomputes it here (see this
        # module's own docstring). Only material changes become a
        # signal (Deliverable 11); `MATERIAL_RISK_APPEARED`/
        # `CASE_CONDITION_TRIGGERED` are excluded by `monitoring_signal`
        # itself (Deliverable 12 -- already covered by sources 1/3
        # above). A ticker with several monitoring changes contributes
        # several signals here, all bundled into that ticker's existing
        # entry -- `_item_for_ticker` already consolidates them into one
        # coherent item alongside every other source (Deliverable 10's
        # own "prefer one coherent item" instruction, already satisfied
        # by the existing consolidation mechanism, not a new one).
        for result in self._monitoring_service.read_model().results:
            if result.case_id is None:
                continue
            is_holding = result.scope.value == "portfolio"
            for change in result.changes:
                signal = monitoring_signal(change.category, change.materiality, is_holding, change.reason)
                if signal is not None:
                    self._ensure(bundles, result.ticker or result.case_id, result.case_id, is_holding).append(signal)

        # 8. Decision Readiness (Atlas Intelligence Sprint 11,
        # Deliverable 10) -- "Decision became ready. Decision became
        # blocked. Operational blocker resolved. Coverage completed.
        # Conflict removed." Every known Case is checked (unlike source
        # 1 above, a readiness change can happen with no Change
        # Intelligence entry -- e.g. Monitoring simply completing for
        # the first time); `change_for_case` itself already guarantees
        # "no event, no timestamp" for an unchanged status (`None`),
        # so nothing here re-filters or re-judges materiality.
        for case_id, ticker in known:
            change = self._decision_readiness_service.change_for_case(case_id, ticker=ticker)
            if change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _decision_readiness_change_reason(resolved_ticker, change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(
                decision_readiness_signal(change.current_status, reason)
            )

        # 9. Investment Decision Synthesis (Atlas Decision Layer
        # Sprint 1, Deliverable 10) -- "changed from Hold to Add,
        # became blocked, became actionable, confidence weakened."
        # Every known Case is checked, same shape as source 8 above;
        # `change_for_case` itself already guarantees "no event, no
        # timestamp" for an unchanged decision (`None`).
        for case_id, ticker in known:
            decision_change = self._investment_decision_service.change_for_case(case_id, ticker=ticker)
            if decision_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _investment_decision_change_reason(resolved_ticker, decision_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(
                investment_decision_signal(decision_change.current_action, decision_change.current_qualifier_kinds, reason)
            )

        # 10. Recommendation Conviction & Strength (Atlas Decision
        # Layer Sprint 2, Deliverable 10) -- "conviction improved.
        # conviction reduced. operational blocker removed. evidence
        # strengthened." Every known Case is checked, same shape as
        # sources 8/9 above; `change_for_case` itself already
        # guarantees "no event, no timestamp" for an unchanged
        # conviction (`None`).
        for case_id, ticker in known:
            conviction_change = self._recommendation_conviction_service.change_for_case(case_id, ticker=ticker)
            if conviction_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _recommendation_conviction_change_reason(resolved_ticker, conviction_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(
                recommendation_conviction_signal(conviction_change.current_stability, reason)
            )

        # 11. Decision Path & Required Progress (Atlas Decision Layer
        # Sprint 3, Deliverable 10) -- "decision path shortened.
        # decision path blocked. operational blocker removed. evidence
        # blocker resolved. dependency resolved." Every known Case is
        # checked, same shape as sources 8/9/10 above; `change_for_case`
        # itself already guarantees "no event, no timestamp" for an
        # unchanged path (`None`).
        for case_id, ticker in known:
            path_change = self._decision_path_service.change_for_case(case_id, ticker=ticker)
            if path_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _decision_path_change_reason(resolved_ticker, path_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(
                decision_path_signal(path_change.current_final_reachable_state, reason)
            )

        # 12. Decision Alternatives & Opportunity Cost (Atlas Decision
        # Layer Sprint 4, Deliverable 10) -- "new alternative became
        # available. alternative disappeared. alternative strengthened.
        # alternative weakened. waiting became preferable." Every known
        # Case is checked, same shape as sources 8/9/10/11 above;
        # `change_for_case` itself already guarantees "no event, no
        # timestamp" for an unchanged alternative set (`None`).
        for case_id, ticker in known:
            opportunity_cost_change = self._opportunity_cost_service.change_for_case(case_id, ticker=ticker)
            if opportunity_cost_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _opportunity_cost_change_reason(resolved_ticker, opportunity_cost_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(opportunity_cost_signal(reason))

        # 13. Decision Memory (Atlas Decision Layer Sprint 5,
        # Deliverable 10) -- "recommendation changed, conviction/
        # readiness/decision path direction, blockers resolved/added,
        # alternative changed" -- always naming which structured field
        # changed and what it changed to. Every known Case is checked,
        # same shape as sources 8/9/10/11/12 above; `change_for_case`
        # itself already guarantees "no event, no timestamp" -- it
        # returns a change only when a genuinely new snapshot row was
        # just appended AND it isn't the Case's own baseline row (see
        # `atlas.alpha.decision_memory.service`). Informational overlap
        # with sources 8-12 is expected and not redundant: this source
        # is Decision Memory's own durable record of the change, those
        # are each layer's own live signal; `_ensure`'s own per-ticker
        # consolidation folds both into one coherent item, never two.
        for case_id, ticker in known:
            memory_change = self._decision_memory_service.change_for_case(case_id, ticker=ticker)
            if memory_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _decision_memory_change_reason(resolved_ticker, memory_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(decision_memory_signal(reason))

        # 14. Decision Explanation & Traceability (Atlas Decision Layer
        # Sprint 6, Deliverable 10) -- "explanation changed, new
        # supporting finding, resolved blocker, supporting evidence
        # expanded" -- always naming which structured field changed
        # and what it changed to. Every known Case is checked, same
        # shape as sources 8-13 above; `change_for_case` itself
        # already guarantees "no event, no timestamp" for an unchanged
        # explanation (`None`). Informational overlap with sources
        # 8-13 is expected and not redundant: this source announces a
        # change to *why* the decision stands as it does, those are
        # each layer's own live content signal; `_ensure`'s own
        # per-ticker consolidation folds both into one coherent item,
        # never two.
        for case_id, ticker in known:
            explanation_change = self._decision_explanation_service.change_for_case(case_id, ticker=ticker)
            if explanation_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _decision_explanation_change_reason(resolved_ticker, explanation_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(decision_explanation_signal(reason))

        # 15. Decision Reliability (Atlas Decision Layer Sprint 7,
        # Deliverable 11) -- "reliability improved, reliability
        # weakened, operational issue resolved, evidence strengthened"
        # -- always naming which structured field changed and what it
        # changed to. Every known Case is checked, same shape as
        # sources 8-14 above; `change_for_case` itself already
        # guarantees "no event, no timestamp" for an unchanged
        # reliability (`None`). Informational overlap with sources
        # 8-14 is expected and not redundant: this source announces a
        # change to *how trustworthy* the decision is, those are each
        # layer's own live content signal; `_ensure`'s own per-ticker
        # consolidation folds both into one coherent item, never two.
        for case_id, ticker in known:
            reliability_change = self._decision_reliability_service.change_for_case(case_id, ticker=ticker)
            if reliability_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _decision_reliability_change_reason(resolved_ticker, reliability_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(decision_reliability_signal(reason))

        # 16. Portfolio Decision Synthesis (Atlas Decision Layer
        # Sprint 8, Deliverable 11) -- "portfolio decision changed,
        # capital competition changed, portfolio conflict resolved,
        # portfolio opportunity appeared" -- always naming which
        # structured field changed and what it changed to. Every known
        # Case is checked, same shape as sources 8-15 above;
        # `change_for_case` itself already guarantees "no event, no
        # timestamp" for an unchanged portfolio decision (`None`).
        # Informational overlap with sources 8-15 is expected and not
        # redundant: this source announces a change to what the
        # decision means for the *portfolio*, those are each layer's
        # own live content signal; `_ensure`'s own per-ticker
        # consolidation folds both into one coherent item, never two.
        for case_id, ticker in known:
            portfolio_decision_change = self._portfolio_decision_service.change_for_case(case_id, ticker=ticker)
            if portfolio_decision_change is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False
            reason = _portfolio_decision_change_reason(resolved_ticker, portfolio_decision_change)
            self._ensure(bundles, resolved_ticker, case_id, is_holding).append(portfolio_decision_signal(reason))

        # 17. Executive Change / Management Credibility / Business
        # Quality (Product Intelligence Sprint 1: Portfolio Intelligence
        # Activation) -- three real Investment Case capabilities
        # (Capability Expansion Sprints 7/8/10) that had never been read
        # by any Portfolio-facing module before this sprint. Every known
        # Case is checked, the same shape as sources 8-16 above, but
        # unlike those this reads `self._composition_service.build`
        # directly rather than a dedicated `change_for_case` detector --
        # none exists for these three capabilities, and building one
        # would be new investment reasoning this sprint's own
        # instructions forbid. `composition_service.build` is memoized
        # for the duration of this call (see this module's own
        # docstring), so calling it again here for a Case sources 1/2
        # already built costs zero additional `InvestmentCaseComposition`
        # builds.
        for case_id, ticker in known:
            composition = self._composition_service.build(case_id)
            if composition is None:
                continue
            resolved_ticker = ticker or case_id
            is_holding = ticker in held_tickers if ticker else False

            # Executive Change: only a leadership change disclosed in
            # the most recent transcript Atlas has for this ticker is
            # "current" -- an older change would have already been
            # surfaced (and, with no persisted "last agenda run" state
            # to compare against, would otherwise fire forever).
            transcripts = composition.earnings_call.transcripts
            if transcripts:
                latest_quarter = transcripts[-1].quarter
                for event in composition.executive_change_intelligence.leadership_changes:
                    if event.source_transcript != latest_quarter:
                        continue
                    event_date = event.effective_date or event.observed_date
                    since = datetime.combine(event_date, datetime.min.time(), tzinfo=timezone.utc)
                    reason = _executive_change_reason(resolved_ticker, event)
                    fact = ReasonFact(
                        ReasonCode.EXECUTIVE_CHANGE,
                        resolved_ticker,
                        value=event.event_type.value,
                        secondary_value=event.role_category.value,
                        label=event.executive_name,
                    )
                    self._ensure(bundles, resolved_ticker, case_id, is_holding).append(
                        executive_change_signal(event.role_category, reason, since, fact=fact)
                    )

            for finding in composition.management_credibility_intelligence.findings:
                fact = ReasonFact(ReasonCode.MANAGEMENT_CREDIBILITY, resolved_ticker, value=finding.kind.value)
                signal = management_credibility_signal(
                    finding.kind, _management_credibility_reason(resolved_ticker, finding.kind), fact=fact
                )
                if signal is not None:
                    self._ensure(bundles, resolved_ticker, case_id, is_holding).append(signal)

            for finding in composition.business_quality_intelligence.findings:
                fact = ReasonFact(ReasonCode.BUSINESS_QUALITY, resolved_ticker, value=finding.kind.value)
                signal = business_quality_signal(finding.kind, _business_quality_reason(resolved_ticker), fact=fact)
                if signal is not None:
                    self._ensure(bundles, resolved_ticker, case_id, is_holding).append(signal)

        return build_agenda(
            bundles,
            portfolio_level_signals,
            holdings_count=len(portfolio_state.holdings) if portfolio_state is not None else 0,
            cash_weight_percent=portfolio_state.cash_weight_percent if portfolio_state is not None else None,
            concentration_level=status_report.summary.concentration_level if status_report.summary is not None else None,
        )
