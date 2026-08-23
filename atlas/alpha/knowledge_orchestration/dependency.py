"""Dependency Planning (Knowledge Orchestration Engine, Phase 3).

Resolves prerequisite chains declared on `ProviderCapability
.prerequisites` into a real execution order -- "Need Regulatory
Filings -> Need SEC Identity -> Need Company Identity" (the brief's
own example) is not a special case here: `sec_edgar_filings`'s own
registry entry names `COMPANY_PROFILE` as a prerequisite, and this
module's plain topological sort handles it identically to any other
domain dependency, present or future.
"""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.models import InvestmentCaseKnowledgeCoverage, KnowledgeDomain
from atlas.alpha.knowledge_orchestration.capability import PROVIDER_CAPABILITIES
from atlas.alpha.knowledge_orchestration.planner import AcquisitionPlanItem, DomainState, classify_domain_state
from atlas.alpha.knowledge_strategy.evaluation import RELEVANCE_RANK

__all__ = ["resolve_order"]


def _domain_states(coverage: InvestmentCaseKnowledgeCoverage) -> dict[KnowledgeDomain, DomainState]:
    return {dc.domain: classify_domain_state(dc) for dc in coverage.domains}


def resolve_order(
    items: tuple[AcquisitionPlanItem, ...], coverage: InvestmentCaseKnowledgeCoverage
) -> tuple[AcquisitionPlanItem, ...]:
    """A plain topological sort: an item whose provider declares a
    prerequisite domain that is *itself* still missing/partial/stale
    sorts after whichever item(s) in this same plan would fill that
    prerequisite. A prerequisite domain that is already `COMPLETE`
    imposes no ordering at all -- Dependency Planning only orders
    around REAL, currently-unmet dependencies, never a domain that
    happens to be named as a prerequisite but is already satisfied.

    Raises `ValueError` on a cycle -- a cycle would be a
    `PROVIDER_CAPABILITIES` authoring bug (two providers each
    declaring the other's domain as a prerequisite), not a real
    runtime data condition, so it must surface loudly.

    Among items with no prerequisite relationship to each other,
    `items` is first sorted by the Knowledge Strategy Engine's own
    Decision Relevance (Phase 3/6: "research order should be driven by
    expected improvement to investment reasoning") -- the topological
    visit below still runs unchanged on this reordered sequence, so a
    hard prerequisite always wins over relevance, never the reverse:
    a `LOW`-relevance domain that happens to be a `CRITICAL` domain's
    own prerequisite is still resolved first."""
    states = _domain_states(coverage)
    domain_to_items: dict[KnowledgeDomain, list[AcquisitionPlanItem]] = {}
    for item in items:
        domain_to_items.setdefault(item.domain, []).append(item)

    resolved: list[AcquisitionPlanItem] = []
    resolved_domains: set[KnowledgeDomain] = set()

    def _unmet_prerequisite_domains(item: AcquisitionPlanItem) -> tuple[KnowledgeDomain, ...]:
        capability = PROVIDER_CAPABILITIES[item.provider_id]
        return tuple(
            prereq
            for prereq in capability.prerequisites
            if states.get(prereq) is not DomainState.COMPLETE and prereq in domain_to_items
        )

    def _visit(item: AcquisitionPlanItem, chain: tuple[KnowledgeDomain, ...]) -> None:
        if item.domain in resolved_domains:
            return
        if item.domain in chain:
            raise ValueError(f"Cyclic provider dependency detected involving domain {item.domain.value!r}")
        for prereq_domain in _unmet_prerequisite_domains(item):
            for prereq_item in domain_to_items[prereq_domain]:
                _visit(prereq_item, (*chain, item.domain))
        if item.domain not in resolved_domains:
            resolved.extend(domain_to_items[item.domain])
            resolved_domains.add(item.domain)

    for item in sorted(items, key=lambda item: RELEVANCE_RANK[item.relevance]):
        _visit(item, ())

    return tuple(resolved)
