"""Tests for `atlas.alpha.knowledge_strategy.relevance` (Phases 1 + 2)."""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_orchestration.capability import DOMAIN_CRITICALITY, DomainCriticality
from atlas.alpha.knowledge_strategy.relevance import (
    DOMAIN_RELEVANCE,
    DecisionRelevance,
    reasons_for,
    relevance_of,
)


class TestRegistryExhaustiveness:
    def test_every_knowledge_domain_has_an_entry(self):
        assert set(DOMAIN_RELEVANCE.keys()) == set(KnowledgeDomain)

    def test_every_entry_has_at_least_one_explaining_reason(self):
        for domain, domain_relevance in DOMAIN_RELEVANCE.items():
            assert len(domain_relevance.reasons) >= 1, domain


class TestGroundedInRealEvaluatorDependencies:
    """`knowledge_orchestration.capability.DOMAIN_CRITICALITY` already
    names the two domains a real, already-running evaluator depends on
    today (`FINANCIAL_HISTORY`/`VALUATION`, confirmed against the real
    evaluator call graph). This engine's own `CRITICAL` tier must agree
    with that existing, independently-verified fact -- both registries
    describe the same underlying reality."""

    def test_every_existing_critical_domain_is_still_critical_here(self):
        for domain, criticality in DOMAIN_CRITICALITY.items():
            if criticality is DomainCriticality.CRITICAL:
                assert relevance_of(domain) is DecisionRelevance.CRITICAL, domain

    def test_case_memory_domains_are_irrelevant(self):
        for domain in (
            KnowledgeDomain.MONITORING_STATUS,
            KnowledgeDomain.HISTORICAL_OBSERVATIONS,
            KnowledgeDomain.EXISTING_EVIDENCE,
            KnowledgeDomain.KNOWLEDGE_REFERENCES,
        ):
            assert relevance_of(domain) is DecisionRelevance.IRRELEVANT


class TestAccessors:
    def test_relevance_of_matches_registry(self):
        assert relevance_of(KnowledgeDomain.FINANCIAL_HISTORY) is DOMAIN_RELEVANCE[KnowledgeDomain.FINANCIAL_HISTORY].relevance

    def test_reasons_for_matches_registry(self):
        assert reasons_for(KnowledgeDomain.VALUATION) == DOMAIN_RELEVANCE[KnowledgeDomain.VALUATION].reasons
