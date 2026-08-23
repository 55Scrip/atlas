"""Tests for `atlas.alpha.knowledge_orchestration.planner` (Phase 1 +
the plan-time half of Phase 5)."""
from __future__ import annotations

from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality.models import EvidenceDominance, EvidenceFreshness
from atlas.alpha.knowledge_coverage.models import (
    DOMAIN_GROUP,
    InvestmentCaseKnowledgeCoverage,
    KnowledgeDomain,
    KnowledgeDomainCoverage,
    MissingKnowledgeReason,
)
from atlas.alpha.knowledge_orchestration.planner import (
    DomainState,
    SufficiencyReason,
    classify_domain_state,
    plan_acquisition,
)
from atlas.alpha.knowledge_strategy.relevance import DecisionRelevance


def _domain_coverage(
    domain: KnowledgeDomain,
    *,
    level: DimensionCoverageLevel,
    freshness: EvidenceFreshness = EvidenceFreshness.NOT_APPLICABLE,
    dominance: EvidenceDominance = EvidenceDominance.NOT_APPLICABLE,
    missing_reasons: tuple[MissingKnowledgeReason, ...] = (),
) -> KnowledgeDomainCoverage:
    return KnowledgeDomainCoverage(
        domain=domain, group=DOMAIN_GROUP[domain], level=level, freshness=freshness, dominance=dominance,
        missing_reasons=missing_reasons,
    )


def _coverage(domains: tuple[KnowledgeDomainCoverage, ...]) -> InvestmentCaseKnowledgeCoverage:
    """Fills in every `KnowledgeDomain` not explicitly given as
    `NOT_APPLICABLE` -- matches the real `assess_knowledge_coverage`
    contract of "always all 36 domains, every call.\""""
    given = {dc.domain: dc for dc in domains}
    all_domains = tuple(
        given.get(d, _domain_coverage(d, level=DimensionCoverageLevel.NOT_APPLICABLE, missing_reasons=(MissingKnowledgeReason.DOMAIN_NOT_YET_WIRED,)))
        for d in KnowledgeDomain
    )
    available = sum(1 for d in all_domains if d.level is DimensionCoverageLevel.AVAILABLE)
    partial = sum(1 for d in all_domains if d.level is DimensionCoverageLevel.PARTIALLY_AVAILABLE)
    not_applicable = tuple(d.domain for d in all_domains if d.level is DimensionCoverageLevel.NOT_APPLICABLE)
    missing = tuple(d.domain for d in all_domains if d.level is DimensionCoverageLevel.UNAVAILABLE)
    return InvestmentCaseKnowledgeCoverage(
        domains=all_domains, available_count=available, partially_available_count=partial,
        applicable_count=len(all_domains) - len(not_applicable), total_domain_count=len(all_domains),
        not_applicable_count=len(not_applicable), missing_domains=missing, not_applicable_domains=not_applicable,
    )


_UNAVAILABLE = DimensionCoverageLevel.UNAVAILABLE
_AVAILABLE = DimensionCoverageLevel.AVAILABLE
_PARTIAL = DimensionCoverageLevel.PARTIALLY_AVAILABLE


class TestClassifyDomainState:
    def test_not_applicable_level_is_not_applicable_state(self):
        dc = _domain_coverage(KnowledgeDomain.EARNINGS, level=DimensionCoverageLevel.NOT_APPLICABLE)
        assert classify_domain_state(dc) is DomainState.NOT_APPLICABLE

    def test_unavailable_level_is_missing_state(self):
        dc = _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE)
        assert classify_domain_state(dc) is DomainState.MISSING

    def test_partially_available_level_is_partial_state(self):
        dc = _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_PARTIAL)
        assert classify_domain_state(dc) is DomainState.PARTIAL

    def test_available_and_fresh_is_complete_state(self):
        dc = _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH)
        assert classify_domain_state(dc) is DomainState.COMPLETE

    def test_available_and_stale_is_stale_state(self):
        dc = _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.STALE)
        assert classify_domain_state(dc) is DomainState.STALE

    def test_available_and_old_is_stale_state(self):
        dc = _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.OLD)
        assert classify_domain_state(dc) is DomainState.STALE


class TestPlanAcquisitionBrandNewCase:
    def test_a_brand_new_case_plans_every_applicable_provider(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_UNAVAILABLE),
            )
        )
        plan = plan_acquisition(coverage)
        assert plan.sufficiency.is_sufficient is False
        provider_ids = {item.provider_id for item in plan.items}
        assert provider_ids == {"alpha_vantage", "sec_edgar", "sec_edgar_filings"}

        by_domain = {item.domain: item for item in plan.items}
        assert by_domain[KnowledgeDomain.FINANCIAL_HISTORY].relevance is DecisionRelevance.CRITICAL
        assert by_domain[KnowledgeDomain.VALUATION].relevance is DecisionRelevance.CRITICAL
        assert by_domain[KnowledgeDomain.COMPANY_PROFILE].relevance is DecisionRelevance.LOW
        assert by_domain[KnowledgeDomain.REGULATORY_FILINGS].relevance is DecisionRelevance.MEDIUM
        assert all(len(item.impact_reasons) >= 1 for item in plan.items)


class TestPlanAcquisitionCompleteCase:
    def test_an_already_complete_case_plans_nothing(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
            )
        )
        plan = plan_acquisition(coverage)
        assert plan.items == ()
        assert plan.sufficiency.is_sufficient is True
        assert plan.sufficiency.reason is SufficiencyReason.ALL_CRITICAL_DOMAINS_COMPLETE


class TestPlanAcquisitionOptionalGapOnly:
    def test_missing_only_an_optional_domain_is_still_sufficient(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_UNAVAILABLE),
            )
        )
        plan = plan_acquisition(coverage)
        assert plan.items == ()
        assert plan.sufficiency.is_sufficient is True
        assert plan.sufficiency.reason is SufficiencyReason.REMAINING_GAPS_NOT_CRITICAL


class TestPlanAcquisitionCriticalGapRemains:
    def test_missing_a_critical_domain_alone_is_not_sufficient(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
            )
        )
        plan = plan_acquisition(coverage)
        assert plan.sufficiency.is_sufficient is False
        assert plan.sufficiency.reason is SufficiencyReason.CRITICAL_GAPS_REMAIN
        assert {item.provider_id for item in plan.items} == {"sec_edgar"}
