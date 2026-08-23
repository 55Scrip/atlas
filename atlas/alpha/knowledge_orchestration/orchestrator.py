"""Intelligent Acquisition -- the execution loop (Knowledge
Orchestration Engine, Phase 4).

Calls `atlas.alpha.business_data_refresh.service.refresh_company_data`
once per planned item, unmodified -- never a second ingestion path.
The one piece of real, load-bearing logic here is Identity Gate
satisfaction: `refresh_company_data` re-runs the Identity Gate against
whichever providers are in *that specific call's own tuple* (see
`capability.py`'s own `ExecutionConstraint.REQUIRES_IDENTITY`
docstring for the verified mechanics), so any item whose provider
declares that constraint is always called together with the fixed
identity-capable provider subset -- never alone.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.business_data_refresh.models import RefreshSummary
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.knowledge_coverage.models import InvestmentCaseKnowledgeCoverage, KnowledgeDomain
from atlas.alpha.knowledge_orchestration.capability import PROVIDER_CAPABILITIES, ExecutionConstraint
from atlas.alpha.knowledge_orchestration.dependency import resolve_order
from atlas.alpha.knowledge_orchestration.planner import AcquisitionPlan, AcquisitionPlanItem
from atlas.alpha.knowledge_orchestration.reanalysis import should_trigger_reanalysis
from atlas.alpha.knowledge_strategy.completion import ResearchCompletionAssessment, assess_research_completion
from atlas.alpha.knowledge_strategy.evaluation import assess_knowledge_gaps
from atlas.alpha.knowledge_strategy.relevance import DecisionRelevance
from atlas.analysis_engine.business_data.providers import BusinessDataProvider

__all__ = ["AcquisitionStepOutcome", "OrchestrationOutcome", "run_orchestrated_acquisition"]

_DECISION_CRITICAL_RELEVANCE = (DecisionRelevance.CRITICAL, DecisionRelevance.HIGH)


@dataclass(frozen=True)
class AcquisitionStepOutcome:
    item: AcquisitionPlanItem
    summary: RefreshSummary
    domain_acquired: bool
    """`True` iff this step's own `RefreshSummary.changed_records`
    contains at least one record tagged with one of the target
    provider's own `supported_source_kinds` -- i.e. this specific step
    actually produced new knowledge for its own planned domain, not
    merely that the underlying HTTP call succeeded."""


@dataclass(frozen=True)
class OrchestrationOutcome:
    plan: AcquisitionPlan
    ordered_items: tuple[AcquisitionPlanItem, ...]
    steps: tuple[AcquisitionStepOutcome, ...]
    acquired_domains: tuple[KnowledgeDomain, ...]
    should_reanalyze: bool
    """A recommendation only -- `MonitoringService.trigger_automatic_
    run()` is never called from this package. The caller (the API
    router) decides whether to act on it, keeping this package free of
    any dependency on `atlas.alpha.monitoring` at all."""
    research_completion: ResearchCompletionAssessment
    """Knowledge Strategy Engine's own Phase 5 Research Completion
    Strategy, applied to whatever this run's own `plan` was built
    against (see this module's own `run_orchestrated_acquisition` for
    the "remaining gaps" derivation) -- an additional explanation
    surfaced alongside `plan.sufficiency`, never a replacement for the
    execution gate that field still drives."""


def _identity_providers(providers_by_id: dict[str, BusinessDataProvider]) -> tuple[BusinessDataProvider, ...]:
    return tuple(
        provider
        for provider_id, provider in providers_by_id.items()
        if ExecutionConstraint.REQUIRES_IDENTITY not in PROVIDER_CAPABILITIES[provider_id].execution_constraints
    )


def _run_step(
    ticker: str,
    item: AcquisitionPlanItem,
    providers_by_id: dict[str, BusinessDataProvider],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
) -> AcquisitionStepOutcome:
    capability = PROVIDER_CAPABILITIES[item.provider_id]
    target_provider = providers_by_id[item.provider_id]

    call_providers: tuple[BusinessDataProvider, ...] = (target_provider,)
    if ExecutionConstraint.REQUIRES_IDENTITY in capability.execution_constraints:
        call_providers = (*call_providers, *_identity_providers(providers_by_id))

    summary = refresh_company_data(ticker, call_providers, repository, identity_gate=identity_gate)
    domain_acquired = any(
        record.document_type in capability.supported_source_kinds for record in summary.changed_records
    )
    return AcquisitionStepOutcome(item=item, summary=summary, domain_acquired=domain_acquired)


def run_orchestrated_acquisition(
    ticker: str,
    plan: AcquisitionPlan,
    coverage: InvestmentCaseKnowledgeCoverage,
    providers_by_id: dict[str, BusinessDataProvider],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
) -> OrchestrationOutcome:
    """Executes `plan` in dependency order. Deliberately does not
    re-run planning mid-loop: `plan_acquisition` already reduced the
    plan to exactly the decision-critical-or-explicitly-needed items
    before this function was ever called (Phase 5's own plan-time
    sufficiency gate) -- there is no meaningful "re-check and shrink
    further" step partway through one already-minimal run. One step's
    failure never blocks another's, the identical provider-isolation
    discipline `refresh_company_data` itself already establishes."""
    ordered_items = resolve_order(plan.items, coverage)
    steps = tuple(
        _run_step(ticker, item, providers_by_id, repository, identity_gate=identity_gate) for item in ordered_items
    )
    acquired_domains = tuple(dict.fromkeys(step.item.domain for step in steps if step.domain_acquired))

    remaining_gaps = tuple(g for g in assess_knowledge_gaps(coverage) if g.domain not in acquired_domains)
    any_decision_critical_blocked = any(
        step.item.relevance in _DECISION_CRITICAL_RELEVANCE and step.summary.provider_errors and not step.domain_acquired
        for step in steps
    )
    research_completion = assess_research_completion(
        remaining_gaps,
        research_was_performed=bool(steps),
        any_decision_critical_step_blocked=any_decision_critical_blocked,
    )
    return OrchestrationOutcome(
        plan=plan,
        ordered_items=ordered_items,
        steps=steps,
        acquired_domains=acquired_domains,
        should_reanalyze=should_trigger_reanalysis(acquired_domains),
        research_completion=research_completion,
    )
