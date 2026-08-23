"""Knowledge Planning (Knowledge Orchestration Engine, Phase 1 + the
plan-time half of Phase 5).

Pure, no I/O: reads an already-computed `InvestmentCaseKnowledgeCoverage`
(`atlas.alpha.knowledge_coverage.assess_knowledge_coverage`'s own
output, never recomputed here) and the Provider Capability Registry,
and produces an `AcquisitionPlan` -- the ordered list of provider calls
worth making, and why. No provider is called from this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.knowledge_coverage.models import (
    DimensionCoverageLevel,
    EvidenceFreshness,
    InvestmentCaseKnowledgeCoverage,
    KnowledgeDomain,
    KnowledgeDomainCoverage,
)
from atlas.alpha.knowledge_orchestration.capability import (
    PROVIDER_CAPABILITIES,
    DomainCriticality,
    criticality_of,
)
from atlas.alpha.knowledge_strategy.relevance import (
    DecisionRelevance,
    ImpactReasonCode,
    reasons_for,
    relevance_of,
)

__all__ = [
    "DomainState",
    "PlanReasonCode",
    "SufficiencyReason",
    "SufficiencyAssessment",
    "AcquisitionPlanItem",
    "AcquisitionPlan",
    "classify_domain_state",
    "plan_acquisition",
]


class DomainState(str, Enum):
    """Phase 1's own five-member vocabulary -- a pure reclassification
    of `KnowledgeDomainCoverage.level`/`.freshness`, never a new
    computation. Deliberately reuses the exact same underlying
    signals `knowledge_coverage` already computes rather than
    re-deriving freshness/completeness a second way."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"
    STALE = "stale"
    NOT_APPLICABLE = "not_applicable"


_STALE_FRESHNESS = (EvidenceFreshness.OLD, EvidenceFreshness.STALE)


def classify_domain_state(domain_coverage: KnowledgeDomainCoverage) -> DomainState:
    if domain_coverage.level is DimensionCoverageLevel.NOT_APPLICABLE:
        return DomainState.NOT_APPLICABLE
    if domain_coverage.level is DimensionCoverageLevel.UNAVAILABLE:
        return DomainState.MISSING
    if domain_coverage.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE:
        return DomainState.PARTIAL
    # AVAILABLE from here on
    if domain_coverage.freshness in _STALE_FRESHNESS:
        return DomainState.STALE
    return DomainState.COMPLETE


class PlanReasonCode(str, Enum):
    """Closed, presence-only -- the same `MissingKnowledgeReason`/
    `EvidenceWarningCode` discipline: a named, structural fact, never
    free text."""

    DOMAIN_MISSING = "domain_missing"
    DOMAIN_PARTIAL = "domain_partial"
    DOMAIN_STALE = "domain_stale"


_REASON_BY_STATE: dict[DomainState, PlanReasonCode] = {
    DomainState.MISSING: PlanReasonCode.DOMAIN_MISSING,
    DomainState.PARTIAL: PlanReasonCode.DOMAIN_PARTIAL,
    DomainState.STALE: PlanReasonCode.DOMAIN_STALE,
}


class SufficiencyReason(str, Enum):
    ALL_CRITICAL_DOMAINS_COMPLETE = "all_critical_domains_complete"
    """Every domain this build of Atlas has a registered evaluator
    dependency for is `COMPLETE` -- further acquisition would only
    reach `OPTIONAL` domains."""
    REMAINING_GAPS_NOT_CRITICAL = "remaining_gaps_not_critical"
    """At least one gap remains, but every remaining gap is
    `OPTIONAL` -- real, named, deliberately not pursued by default."""
    CRITICAL_GAPS_REMAIN = "critical_gaps_remain"
    """At least one `CRITICAL` domain is not yet `COMPLETE` -- the
    plan is genuinely not empty."""
    NO_PROVIDER_AVAILABLE_FOR_GAP = "no_provider_available_for_gap"
    """A real, honest state: a domain is missing/partial/stale but no
    provider in the current registry supports it (true for 32 of 36
    domains today) -- named explicitly rather than silently omitted."""


@dataclass(frozen=True)
class SufficiencyAssessment:
    is_sufficient: bool
    reason: SufficiencyReason


@dataclass(frozen=True)
class AcquisitionPlanItem:
    domain: KnowledgeDomain
    provider_id: str
    criticality: DomainCriticality
    reason: PlanReasonCode
    relevance: DecisionRelevance = DecisionRelevance.MEDIUM
    """Knowledge Strategy Engine's own Decision Relevance for this
    domain (Phase 1/6 of the Knowledge Strategy & Decision-Critical
    Research sprint) -- consumed by `dependency.resolve_order` as the
    research-priority tie-break among items with no prerequisite
    relationship. Independent of `criticality`: that field still drives
    the existing plan-time sufficiency gate below, unchanged."""
    impact_reasons: tuple[ImpactReasonCode, ...] = ()
    """Why `relevance` was assigned -- Phase 2/4's own "priority should
    always be explainable.\""""


@dataclass(frozen=True)
class AcquisitionPlan:
    items: tuple[AcquisitionPlanItem, ...]
    """Unordered as produced by this module -- `dependency.py::
    resolve_order` produces the final execution order. Empty exactly
    when `sufficiency.is_sufficient` is `True`."""
    sufficiency: SufficiencyAssessment


def _providers_for_domain(domain: KnowledgeDomain) -> tuple[str, ...]:
    return tuple(
        provider_id
        for provider_id, capability in PROVIDER_CAPABILITIES.items()
        if domain in capability.supported_domains
    )


def plan_acquisition(coverage: InvestmentCaseKnowledgeCoverage) -> AcquisitionPlan:
    """Deterministic: identical `coverage` always produces a deeply
    equal `AcquisitionPlan`. Only ever considers a domain this build
    of Atlas has BOTH a registered `DomainCriticality` AND at least one
    registered provider for -- a domain with neither is honestly
    outside this plan's scope, not silently assumed irrelevant."""
    critical_incomplete = False
    unsupported_gap = False
    items: list[AcquisitionPlanItem] = []

    for domain_coverage in coverage.domains:
        criticality = criticality_of(domain_coverage.domain)
        if criticality is None:
            continue  # no registered provider/criticality opinion for this domain at all

        state = classify_domain_state(domain_coverage)
        if state in (DomainState.COMPLETE, DomainState.NOT_APPLICABLE):
            continue

        if criticality is DomainCriticality.CRITICAL:
            critical_incomplete = True

        provider_ids = _providers_for_domain(domain_coverage.domain)
        if not provider_ids:
            unsupported_gap = True
            continue

        reason = _REASON_BY_STATE[state]
        for provider_id in provider_ids:
            items.append(
                AcquisitionPlanItem(
                    domain=domain_coverage.domain,
                    provider_id=provider_id,
                    criticality=criticality,
                    reason=reason,
                    relevance=relevance_of(domain_coverage.domain),
                    impact_reasons=reasons_for(domain_coverage.domain),
                )
            )

    if not critical_incomplete:
        # Phase 5's own plan-time sufficiency gate: every CRITICAL
        # domain is COMPLETE, so no item is worth acquiring by
        # default, regardless of how many OPTIONAL gaps remain --
        # "maximize useful knowledge, not provider execution."
        if items:
            return AcquisitionPlan(
                items=(), sufficiency=SufficiencyAssessment(True, SufficiencyReason.REMAINING_GAPS_NOT_CRITICAL)
            )
        return AcquisitionPlan(
            items=(), sufficiency=SufficiencyAssessment(True, SufficiencyReason.ALL_CRITICAL_DOMAINS_COMPLETE)
        )

    if unsupported_gap and not items:
        return AcquisitionPlan(
            items=(), sufficiency=SufficiencyAssessment(False, SufficiencyReason.NO_PROVIDER_AVAILABLE_FOR_GAP)
        )

    return AcquisitionPlan(items=tuple(items), sufficiency=SufficiencyAssessment(False, SufficiencyReason.CRITICAL_GAPS_REMAIN))
