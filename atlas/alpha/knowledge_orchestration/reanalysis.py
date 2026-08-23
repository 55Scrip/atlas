"""Re-analysis Strategy (Knowledge Orchestration Engine, Phase 6).

A pure gate the orchestrator applies *before* deciding whether to call
`atlas.alpha.monitoring.service.MonitoringService.trigger_automatic_run()`
-- itself never modified, never called from here directly (that stays
the caller's own responsibility, exactly mirroring how the Ingestion
Framework sprint's own automatic triggers call it as a black box).
`MonitoringService`'s own internals (`needs_recompute`, `_evaluate_case`,
the process lock) are never touched or reasoned about here.
"""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_orchestration.capability import DomainCriticality, criticality_of

__all__ = ["should_trigger_reanalysis"]


def should_trigger_reanalysis(acquired_domains: tuple[KnowledgeDomain, ...]) -> bool:
    """`True` only when at least one newly-acquired domain is
    `CRITICAL` -- a real evaluator depends on it, so reasoning could
    genuinely change. A new company description or filing list alone
    (both `OPTIONAL` today, confirmed against the real evaluator call
    graph) never triggers a re-analysis by itself."""
    return any(criticality_of(domain) is DomainCriticality.CRITICAL for domain in acquired_domains)
