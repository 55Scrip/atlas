"""Tests for `atlas.alpha.knowledge_strategy.completion` (Phase 5)."""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_strategy.completion import ResearchCompletionOutcome, assess_research_completion
from atlas.alpha.knowledge_strategy.evaluation import KnowledgeGapAssessment
from atlas.alpha.knowledge_strategy.relevance import DecisionRelevance, ImpactReasonCode


def _gap(domain: KnowledgeDomain, relevance: DecisionRelevance) -> KnowledgeGapAssessment:
    return KnowledgeGapAssessment(domain=domain, relevance=relevance, reasons=(ImpactReasonCode.NOT_YET_CONSUMED_BY_ANY_EVALUATOR,))


class TestDecisionReady:
    def test_no_remaining_gaps_at_all_is_decision_ready(self):
        assessment = assess_research_completion((), research_was_performed=True, any_decision_critical_step_blocked=False)
        assert assessment.outcome is ResearchCompletionOutcome.DECISION_READY


class TestCriticalResearchCompleted:
    def test_research_ran_and_only_low_tier_gaps_remain(self):
        remaining = (_gap(KnowledgeDomain.COMPANY_PROFILE, DecisionRelevance.LOW),)
        assessment = assess_research_completion(remaining, research_was_performed=True, any_decision_critical_step_blocked=False)
        assert assessment.outcome is ResearchCompletionOutcome.CRITICAL_RESEARCH_COMPLETED


class TestRemainingGapsNotDecisionCritical:
    def test_no_research_ran_and_only_low_tier_gaps_existed(self):
        remaining = (_gap(KnowledgeDomain.COMPANY_PROFILE, DecisionRelevance.LOW),)
        assessment = assess_research_completion(remaining, research_was_performed=False, any_decision_critical_step_blocked=False)
        assert assessment.outcome is ResearchCompletionOutcome.REMAINING_GAPS_NOT_DECISION_CRITICAL


class TestAwaitFutureExternalInformation:
    def test_decision_critical_gap_remains_with_no_blocking_error(self):
        remaining = (_gap(KnowledgeDomain.FINANCIAL_HISTORY, DecisionRelevance.CRITICAL),)
        assessment = assess_research_completion(remaining, research_was_performed=True, any_decision_critical_step_blocked=False)
        assert assessment.outcome is ResearchCompletionOutcome.AWAIT_FUTURE_EXTERNAL_INFORMATION


class TestResearchBlockedByUnavailableSources:
    def test_decision_critical_gap_remains_because_a_provider_failed(self):
        remaining = (_gap(KnowledgeDomain.VALUATION, DecisionRelevance.CRITICAL),)
        assessment = assess_research_completion(remaining, research_was_performed=True, any_decision_critical_step_blocked=True)
        assert assessment.outcome is ResearchCompletionOutcome.RESEARCH_BLOCKED_BY_UNAVAILABLE_SOURCES


class TestHighRelevanceCountsAsDecisionCriticalToo:
    def test_a_high_relevance_gap_alone_is_not_yet_decision_ready(self):
        remaining = (_gap(KnowledgeDomain.EARNINGS_CALL_ANALYSIS, DecisionRelevance.HIGH),)
        assessment = assess_research_completion(remaining, research_was_performed=True, any_decision_critical_step_blocked=False)
        assert assessment.outcome is ResearchCompletionOutcome.AWAIT_FUTURE_EXTERNAL_INFORMATION
