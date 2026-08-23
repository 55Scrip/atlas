"""Tests for `atlas.alpha.knowledge_strategy.evaluation` (Phase 2
applied to one Case's own current coverage)."""
from __future__ import annotations

from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality.models import EvidenceFreshness
from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_strategy.evaluation import assess_knowledge_gaps
from atlas.alpha.knowledge_strategy.relevance import DecisionRelevance
from tests.unit.alpha.knowledge_orchestration.test_planner import _coverage, _domain_coverage

_UNAVAILABLE = DimensionCoverageLevel.UNAVAILABLE
_AVAILABLE = DimensionCoverageLevel.AVAILABLE
_PARTIAL = DimensionCoverageLevel.PARTIALLY_AVAILABLE


class TestAssessKnowledgeGaps:
    def test_only_actual_gaps_are_included(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_UNAVAILABLE),
            )
        )
        gaps = assess_knowledge_gaps(coverage)
        domains = {g.domain for g in gaps}
        assert KnowledgeDomain.FINANCIAL_HISTORY not in domains  # COMPLETE, not a gap
        assert KnowledgeDomain.VALUATION in domains
        assert KnowledgeDomain.COMPANY_PROFILE not in domains  # NOT_APPLICABLE, not a gap

    def test_partial_and_stale_both_count_as_gaps(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_PARTIAL),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_AVAILABLE, freshness=EvidenceFreshness.STALE),
            )
        )
        gaps = {g.domain for g in assess_knowledge_gaps(coverage)}
        assert gaps == {KnowledgeDomain.FINANCIAL_HISTORY, KnowledgeDomain.VALUATION}

    def test_gaps_are_ordered_highest_relevance_first(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_UNAVAILABLE),  # LOW
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),  # CRITICAL
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_UNAVAILABLE),  # MEDIUM
            )
        )
        gaps = assess_knowledge_gaps(coverage)
        relevances = [g.relevance for g in gaps]
        assert relevances == sorted(relevances, key=lambda r: _RANK[r])
        assert gaps[0].relevance is DecisionRelevance.CRITICAL

    def test_every_gap_carries_at_least_one_reason(self):
        coverage = _coverage((_domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),))
        gaps = assess_knowledge_gaps(coverage)
        assert all(len(g.reasons) >= 1 for g in gaps)

    def test_an_already_complete_case_has_no_gaps(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
            )
        )
        assert assess_knowledge_gaps(coverage) == ()


_RANK = {
    DecisionRelevance.CRITICAL: 0,
    DecisionRelevance.HIGH: 1,
    DecisionRelevance.MEDIUM: 2,
    DecisionRelevance.LOW: 3,
    DecisionRelevance.IRRELEVANT: 4,
}
