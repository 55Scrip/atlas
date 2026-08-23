"""Decision Relevance Evaluation (Knowledge Strategy Engine, Phase 2)
applied to one Case's own current `InvestmentCaseKnowledgeCoverage`.

Pure, no I/O: filters to domains that are actually a gap right now
(mirrors `knowledge_orchestration.planner.classify_domain_state`'s own
gap definition -- MISSING/PARTIAL/STALE -- reimplemented locally rather
than imported, so this package stays a dependency-free leaf that
`knowledge_orchestration` can safely consume: "Knowledge Strategy
determines what research is worth performing. Knowledge Orchestration
determines how research is performed" only holds if the dependency
points one way), pairs each with its static `DomainRelevance` profile,
and orders the result highest-relevance first -- the research priority
order Phase 3/6 asks `knowledge_orchestration` to consume.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.knowledge_coverage.models import (
    DimensionCoverageLevel,
    EvidenceFreshness,
    InvestmentCaseKnowledgeCoverage,
    KnowledgeDomain,
    KnowledgeDomainCoverage,
)
from atlas.alpha.knowledge_strategy.relevance import DOMAIN_RELEVANCE, DecisionRelevance, ImpactReasonCode

__all__ = ["KnowledgeGapAssessment", "RELEVANCE_RANK", "assess_knowledge_gaps"]

RELEVANCE_RANK: dict[DecisionRelevance, int] = {
    DecisionRelevance.CRITICAL: 0,
    DecisionRelevance.HIGH: 1,
    DecisionRelevance.MEDIUM: 2,
    DecisionRelevance.LOW: 3,
    DecisionRelevance.IRRELEVANT: 4,
}
"""Lower rank = researched first. The single source of truth for
"expected improvement to investment reasoning" ordering -- both this
module's own `assess_knowledge_gaps` and `knowledge_orchestration
.dependency.resolve_order`'s relevance tie-break read the same table."""

_STALE_FRESHNESS = (EvidenceFreshness.OLD, EvidenceFreshness.STALE)


def _is_gap(domain_coverage: KnowledgeDomainCoverage) -> bool:
    if domain_coverage.level in (DimensionCoverageLevel.UNAVAILABLE, DimensionCoverageLevel.PARTIALLY_AVAILABLE):
        return True
    return domain_coverage.level is DimensionCoverageLevel.AVAILABLE and domain_coverage.freshness in _STALE_FRESHNESS


@dataclass(frozen=True)
class KnowledgeGapAssessment:
    domain: KnowledgeDomain
    relevance: DecisionRelevance
    reasons: tuple[ImpactReasonCode, ...]


def assess_knowledge_gaps(coverage: InvestmentCaseKnowledgeCoverage) -> tuple[KnowledgeGapAssessment, ...]:
    gaps = [dc for dc in coverage.domains if _is_gap(dc)]
    assessments = [
        KnowledgeGapAssessment(
            domain=dc.domain,
            relevance=DOMAIN_RELEVANCE[dc.domain].relevance,
            reasons=DOMAIN_RELEVANCE[dc.domain].reasons,
        )
        for dc in gaps
    ]
    return tuple(sorted(assessments, key=lambda a: RELEVANCE_RANK[a.relevance]))
