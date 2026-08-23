"""Tests for `atlas.alpha.knowledge_orchestration.dependency` (Phase 3)."""
from __future__ import annotations

import pytest

from atlas.alpha.coverage.models import DimensionCoverageLevel
from atlas.alpha.evidence_quality.models import EvidenceFreshness
from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_orchestration.dependency import resolve_order
from atlas.alpha.knowledge_orchestration.planner import AcquisitionPlanItem, PlanReasonCode
from atlas.alpha.knowledge_orchestration.capability import DomainCriticality
from atlas.alpha.knowledge_strategy.relevance import reasons_for, relevance_of
from tests.unit.alpha.knowledge_orchestration.test_planner import _coverage, _domain_coverage

_UNAVAILABLE = DimensionCoverageLevel.UNAVAILABLE
_AVAILABLE = DimensionCoverageLevel.AVAILABLE


def _item(domain: KnowledgeDomain, provider_id: str, criticality=DomainCriticality.CRITICAL) -> AcquisitionPlanItem:
    return AcquisitionPlanItem(
        domain=domain,
        provider_id=provider_id,
        criticality=criticality,
        reason=PlanReasonCode.DOMAIN_MISSING,
        relevance=relevance_of(domain),
        impact_reasons=reasons_for(domain),
    )


class TestPrerequisiteOrdering:
    def test_financial_history_sorts_after_company_profile_when_both_are_missing(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
            )
        )
        items = (
            _item(KnowledgeDomain.FINANCIAL_HISTORY, "sec_edgar"),
            _item(KnowledgeDomain.COMPANY_PROFILE, "alpha_vantage", DomainCriticality.OPTIONAL),
        )
        ordered = resolve_order(items, coverage)
        provider_order = [i.provider_id for i in ordered]
        assert provider_order.index("alpha_vantage") < provider_order.index("sec_edgar")

    def test_no_reordering_needed_when_prerequisite_is_already_complete(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
            )
        )
        items = (_item(KnowledgeDomain.FINANCIAL_HISTORY, "sec_edgar"),)
        ordered = resolve_order(items, coverage)
        assert ordered == items

    def test_all_three_default_providers_order_identity_first(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_UNAVAILABLE),
            )
        )
        items = (
            _item(KnowledgeDomain.REGULATORY_FILINGS, "sec_edgar_filings", DomainCriticality.OPTIONAL),
            _item(KnowledgeDomain.FINANCIAL_HISTORY, "sec_edgar"),
            _item(KnowledgeDomain.VALUATION, "alpha_vantage"),
            _item(KnowledgeDomain.COMPANY_PROFILE, "alpha_vantage", DomainCriticality.OPTIONAL),
        )
        ordered = resolve_order(items, coverage)
        provider_order = [i.provider_id for i in ordered]
        assert provider_order.index("alpha_vantage") < provider_order.index("sec_edgar")
        assert provider_order.index("alpha_vantage") < provider_order.index("sec_edgar_filings")


class TestRelevanceTieBreak:
    """Phase 3/6 of the Knowledge Strategy sprint: among items with no
    prerequisite relationship to each other, higher Decision Relevance
    is researched first."""

    def test_critical_relevance_domain_sorts_before_medium_relevance_domain_with_no_shared_dependency(self):
        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.COMPANY_PROFILE, level=_AVAILABLE, freshness=EvidenceFreshness.FRESH),
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),  # CRITICAL relevance
                _domain_coverage(KnowledgeDomain.REGULATORY_FILINGS, level=_UNAVAILABLE),  # MEDIUM relevance
            )
        )
        # Deliberately listed in the "wrong" (lower-relevance-first) order --
        # `resolve_order` must still put FINANCIAL_HISTORY first.
        items = (
            _item(KnowledgeDomain.REGULATORY_FILINGS, "sec_edgar_filings", DomainCriticality.OPTIONAL),
            _item(KnowledgeDomain.FINANCIAL_HISTORY, "sec_edgar"),
        )
        ordered = resolve_order(items, coverage)
        provider_order = [i.provider_id for i in ordered]
        assert provider_order.index("sec_edgar") < provider_order.index("sec_edgar_filings")


class TestCycleDetection:
    def test_a_genuine_cycle_raises_value_error(self, monkeypatch):
        import atlas.alpha.knowledge_orchestration.dependency as dependency_module

        fake_capabilities = {
            "provider_a": type("Cap", (), {"prerequisites": (KnowledgeDomain.VALUATION,)})(),
            "provider_b": type("Cap", (), {"prerequisites": (KnowledgeDomain.FINANCIAL_HISTORY,)})(),
        }
        monkeypatch.setattr(dependency_module, "PROVIDER_CAPABILITIES", fake_capabilities)

        coverage = _coverage(
            (
                _domain_coverage(KnowledgeDomain.FINANCIAL_HISTORY, level=_UNAVAILABLE),
                _domain_coverage(KnowledgeDomain.VALUATION, level=_UNAVAILABLE),
            )
        )
        items = (
            _item(KnowledgeDomain.FINANCIAL_HISTORY, "provider_a"),
            _item(KnowledgeDomain.VALUATION, "provider_b"),
        )
        with pytest.raises(ValueError):
            resolve_order(items, coverage)
