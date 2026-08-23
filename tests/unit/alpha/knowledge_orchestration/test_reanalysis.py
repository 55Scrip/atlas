"""Tests for `atlas.alpha.knowledge_orchestration.reanalysis` (Phase 6)."""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_orchestration.reanalysis import should_trigger_reanalysis


class TestShouldTriggerReanalysis:
    def test_financial_history_alone_triggers_reanalysis(self):
        assert should_trigger_reanalysis((KnowledgeDomain.FINANCIAL_HISTORY,)) is True

    def test_valuation_alone_triggers_reanalysis(self):
        assert should_trigger_reanalysis((KnowledgeDomain.VALUATION,)) is True

    def test_company_profile_alone_does_not_trigger_reanalysis(self):
        assert should_trigger_reanalysis((KnowledgeDomain.COMPANY_PROFILE,)) is False

    def test_regulatory_filings_alone_does_not_trigger_reanalysis(self):
        assert should_trigger_reanalysis((KnowledgeDomain.REGULATORY_FILINGS,)) is False

    def test_optional_and_critical_together_still_triggers(self):
        assert should_trigger_reanalysis((KnowledgeDomain.COMPANY_PROFILE, KnowledgeDomain.FINANCIAL_HISTORY)) is True

    def test_no_domains_acquired_does_not_trigger(self):
        assert should_trigger_reanalysis(()) is False

    def test_a_domain_with_no_registered_provider_never_triggers_on_its_own(self):
        assert should_trigger_reanalysis((KnowledgeDomain.EARNINGS_CALL_ANALYSIS,)) is False
