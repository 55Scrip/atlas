"""Tests for `atlas.alpha.knowledge_orchestration.capability` -- the
Provider Capability Registry (Phase 2)."""
from __future__ import annotations

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_orchestration.capability import (
    DOMAIN_CRITICALITY,
    PROVIDER_CAPABILITIES,
    DomainCriticality,
    ExecutionConstraint,
    capability_for,
    criticality_of,
)


class TestRegistryCompleteness:
    def test_every_capability_entry_supports_at_least_one_real_domain(self):
        for provider_id, capability in PROVIDER_CAPABILITIES.items():
            assert len(capability.supported_domains) > 0
            for domain in capability.supported_domains:
                assert isinstance(domain, KnowledgeDomain)

    def test_provider_id_field_matches_its_own_registry_key(self):
        for key, capability in PROVIDER_CAPABILITIES.items():
            assert capability.provider_id == key


class TestIdentityConstraint:
    def test_alpha_vantage_does_not_require_identity(self):
        assert ExecutionConstraint.REQUIRES_IDENTITY not in PROVIDER_CAPABILITIES["alpha_vantage"].execution_constraints

    def test_sec_edgar_requires_identity(self):
        assert ExecutionConstraint.REQUIRES_IDENTITY in PROVIDER_CAPABILITIES["sec_edgar"].execution_constraints

    def test_sec_edgar_filings_requires_identity(self):
        assert ExecutionConstraint.REQUIRES_IDENTITY in PROVIDER_CAPABILITIES["sec_edgar_filings"].execution_constraints


class TestPrerequisites:
    def test_sec_edgar_and_sec_edgar_filings_both_prerequire_company_profile(self):
        assert PROVIDER_CAPABILITIES["sec_edgar"].prerequisites == (KnowledgeDomain.COMPANY_PROFILE,)
        assert PROVIDER_CAPABILITIES["sec_edgar_filings"].prerequisites == (KnowledgeDomain.COMPANY_PROFILE,)

    def test_alpha_vantage_has_no_prerequisites(self):
        assert PROVIDER_CAPABILITIES["alpha_vantage"].prerequisites == ()


class TestDomainCriticality:
    def test_financial_history_and_valuation_are_critical(self):
        assert criticality_of(KnowledgeDomain.FINANCIAL_HISTORY) is DomainCriticality.CRITICAL
        assert criticality_of(KnowledgeDomain.VALUATION) is DomainCriticality.CRITICAL

    def test_company_profile_and_regulatory_filings_are_optional(self):
        assert criticality_of(KnowledgeDomain.COMPANY_PROFILE) is DomainCriticality.OPTIONAL
        assert criticality_of(KnowledgeDomain.REGULATORY_FILINGS) is DomainCriticality.OPTIONAL

    def test_a_domain_with_no_registered_provider_has_no_criticality_opinion(self):
        assert criticality_of(KnowledgeDomain.MANAGEMENT) is None

    def test_every_domain_criticality_key_has_a_provider(self):
        for domain in DOMAIN_CRITICALITY:
            providers = [c for c in PROVIDER_CAPABILITIES.values() if domain in c.supported_domains]
            assert len(providers) > 0, f"{domain} has a criticality opinion but no registered provider"


class TestCapabilityFor:
    def test_unknown_provider_id_returns_none(self):
        assert capability_for("nonexistent_provider") is None

    def test_known_provider_id_returns_its_capability(self):
        assert capability_for("sec_edgar").provider_id == "sec_edgar"
