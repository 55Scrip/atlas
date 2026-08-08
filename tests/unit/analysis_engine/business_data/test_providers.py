"""Tests for `atlas.analysis_engine.business_data.providers`
(ATLAS-022 Phase 4) -- the Provider contract, exercised against the
one real (if trivial) implementation this sprint ships."""
from __future__ import annotations

from atlas.analysis_engine.business_data.providers import BusinessDataProvider, StaticBusinessDataProvider
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT, build_raw_document


class TestStaticBusinessDataProviderConformsToTheProtocol:
    def test_is_a_structural_match_for_business_data_provider(self):
        provider = StaticBusinessDataProvider()
        assert isinstance(provider, BusinessDataProvider)

    def test_fetch_returns_only_documents_for_the_requested_company(self):
        asml_doc = build_raw_document(company="ASML")
        besi_doc = build_raw_document(company="BESI", identifier="besi-doc")
        provider = StaticBusinessDataProvider(documents=(asml_doc, besi_doc))
        result = provider.fetch(company_identifier="ASML", evaluated_at=EVALUATED_AT)
        assert result == (asml_doc,)

    def test_fetch_returns_empty_tuple_for_an_unknown_company(self):
        provider = StaticBusinessDataProvider(documents=(build_raw_document(company="ASML"),))
        assert provider.fetch(company_identifier="NOBODY", evaluated_at=EVALUATED_AT) == ()

    def test_fetch_returns_multiple_documents_for_the_same_company(self):
        doc_a = build_raw_document(identifier="doc-a")
        doc_b = build_raw_document(identifier="doc-b")
        provider = StaticBusinessDataProvider(documents=(doc_a, doc_b))
        result = provider.fetch(company_identifier="ASML", evaluated_at=EVALUATED_AT)
        assert {doc.identifier for doc in result} == {"doc-a", "doc-b"}


class TestDeterminism:
    def test_identical_calls_produce_identical_results(self):
        provider = StaticBusinessDataProvider(documents=(build_raw_document(),))
        first = provider.fetch(company_identifier="ASML", evaluated_at=EVALUATED_AT)
        second = provider.fetch(company_identifier="ASML", evaluated_at=EVALUATED_AT)
        assert first == second

    def test_no_network_or_file_io_anywhere_in_this_module(self):
        import inspect

        from atlas.analysis_engine.business_data import providers

        source = inspect.getsource(providers)
        for forbidden in ("urlopen", "requests.", "open(", "socket."):
            assert forbidden not in source
