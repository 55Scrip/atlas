"""Tests for `atlas.alpha.knowledge_provider.contract.KnowledgeProvider`
-- confirms the additive dual-satisfaction claim: a real `KnowledgeProvider`
structurally satisfies `BusinessDataProvider` too, so it drops into the
existing per-provider ingestion loop unmodified.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_provider import KnowledgeProvider
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.analysis_engine.business_data.sources import SourceKind

_NOW = datetime(2026, 8, 22, tzinfo=timezone.utc)


class _FakeKnowledgeProvider:
    provider_id = "fake_provider"
    supported_domains = (KnowledgeDomain.REGULATORY_FILINGS,)
    supported_source_kinds = (SourceKind.COMPANY_FILING,)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        return ()


class TestKnowledgeProviderContract:
    def test_a_real_provider_satisfies_knowledge_provider(self):
        provider = _FakeKnowledgeProvider()
        assert isinstance(provider, KnowledgeProvider)

    def test_a_real_knowledge_provider_also_satisfies_business_data_provider(self):
        """The additive claim this whole framework depends on: a
        `KnowledgeProvider` never needs a second, parallel ingestion
        path -- it IS a `BusinessDataProvider` too, by structure."""
        provider = _FakeKnowledgeProvider()
        assert isinstance(provider, BusinessDataProvider)

    def test_provider_declares_its_own_identity_and_domains(self):
        provider = _FakeKnowledgeProvider()
        assert provider.provider_id == "fake_provider"
        assert provider.supported_domains == (KnowledgeDomain.REGULATORY_FILINGS,)
        assert provider.supported_source_kinds == (SourceKind.COMPANY_FILING,)

    def test_fetch_returns_a_tuple_of_raw_business_documents(self):
        provider = _FakeKnowledgeProvider()
        result = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert result == ()

    def test_an_object_missing_a_required_property_does_not_satisfy_the_protocol(self):
        class _Incomplete:
            provider_id = "incomplete"

            def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple:
                return ()

        assert not isinstance(_Incomplete(), KnowledgeProvider)
