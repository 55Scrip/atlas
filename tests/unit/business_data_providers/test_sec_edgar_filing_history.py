"""`SecEdgarFilingHistoryProvider` contract tests (Automatic Knowledge
Ingestion Framework, Foundation Provider).

All fake -- no live network anywhere in this file. Mirrors
`test_sec_edgar.py`'s own `_fake_fetcher` injectable pattern exactly.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.business_data_providers.errors import (
    CompanyNotFound,
    MalformedProviderResponse,
    MissingRequiredField,
)
from atlas.business_data_providers.sec_edgar import SecEdgarFilingHistoryProvider

_NOW = datetime(2026, 8, 22, tzinfo=timezone.utc)

_TICKER_MAP = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
}

_REAL_SHAPE_SUBMISSIONS = {
    "cik": "320193",
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "accessionNumber": ["0000320193-26-000010", "0000320193-26-000005", "0000320193-25-000090"],
            "filingDate": ["2026-08-01", "2026-05-01", "2025-11-01"],
            "reportDate": ["2026-06-27", "2026-03-28", "2025-09-27"],
            "form": ["10-Q", "10-Q", "10-K"],
            "primaryDocument": ["aapl-20260627.htm", "aapl-20260328.htm", "aapl-20250927.htm"],
        },
        "files": [],
    },
}


def _fake_fetcher(responses: dict[str, object]):
    def fetcher(url: str, headers: dict | None) -> object:
        for key, value in responses.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value
        raise AssertionError(f"unexpected URL in test: {url}")

    return fetcher


class TestProviderContract:
    def test_provider_identity_and_domains(self):
        provider = SecEdgarFilingHistoryProvider()
        assert provider.provider_id == "sec_edgar_filings"
        assert provider.supported_domains == (KnowledgeDomain.REGULATORY_FILINGS,)
        assert provider.supported_source_kinds == (SourceKind.COMPANY_FILING,)


class TestCompanyResolution:
    def test_unknown_ticker_raises_company_not_found(self):
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP})
        provider = SecEdgarFilingHistoryProvider(fetcher)
        with pytest.raises(CompanyNotFound):
            provider.fetch(company_identifier="NOPE", evaluated_at=_NOW)


class TestFetch:
    def test_real_shape_submissions_produces_one_document_per_tracked_form(self):
        fetcher = _fake_fetcher(
            {"company_tickers.json": _TICKER_MAP, "submissions/CIK": _REAL_SHAPE_SUBMISSIONS}
        )
        provider = SecEdgarFilingHistoryProvider(fetcher)
        documents = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(documents) == 3
        assert all(isinstance(d, RawBusinessDocument) for d in documents)
        assert all(d.source_kind == SourceKind.COMPANY_FILING.value for d in documents)

    def test_untracked_form_types_are_excluded(self):
        submissions = {
            "cik": "320193",
            "filings": {
                "recent": {
                    "accessionNumber": ["0000320193-26-000001", "0000320193-26-000002"],
                    "filingDate": ["2026-08-01", "2026-08-02"],
                    "reportDate": ["", ""],
                    "form": ["4", "10-K"],
                    "primaryDocument": ["form4.xml", "aapl-10k.htm"],
                }
            },
        }
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "submissions/CIK": submissions})
        provider = SecEdgarFilingHistoryProvider(fetcher)
        documents = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(documents) == 1
        assert documents[0].metadata["form_type"] == "10-K"

    def test_def_14a_is_tracked_alongside_10k_10q_8k(self):
        """(Capability Expansion Sprint 12: Incentive Intelligence) The
        one, minimal, additive registry change that sprint made -- see
        `incentive_intelligence.py`'s own module docstring for why."""
        submissions = {
            "cik": "320193",
            "filings": {
                "recent": {
                    "accessionNumber": ["0000320193-26-000003", "0000320193-26-000004"],
                    "filingDate": ["2026-01-15", "2026-08-02"],
                    "reportDate": ["", ""],
                    "form": ["DEF 14A", "4"],
                    "primaryDocument": ["aapl-proxy.htm", "form4.xml"],
                }
            },
        }
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "submissions/CIK": submissions})
        provider = SecEdgarFilingHistoryProvider(fetcher)
        documents = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(documents) == 1
        assert documents[0].metadata["form_type"] == "DEF 14A"

    def test_each_document_carries_real_metadata(self):
        fetcher = _fake_fetcher(
            {"company_tickers.json": _TICKER_MAP, "submissions/CIK": _REAL_SHAPE_SUBMISSIONS}
        )
        provider = SecEdgarFilingHistoryProvider(fetcher)
        documents = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        ten_k = next(d for d in documents if d.metadata["form_type"] == "10-K")
        assert ten_k.metadata["accession_number"] == "0000320193-25-000090"
        assert ten_k.metadata["sec_cik"] == "0000320193"
        assert ten_k.identifier == "AAPL:FILING:0000320193-25-000090"
        assert ten_k.period_end.isoformat() == "2025-09-27"
        assert "aapl-20250927.htm" in ten_k.raw_reference

    def test_missing_recent_filings_raises_missing_required_field(self):
        submissions = {"cik": "320193", "filings": {"recent": {}}}
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "submissions/CIK": submissions})
        provider = SecEdgarFilingHistoryProvider(fetcher)
        with pytest.raises(MissingRequiredField):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_mismatched_parallel_arrays_raises_malformed(self):
        submissions = {
            "cik": "320193",
            "filings": {
                "recent": {
                    "accessionNumber": ["0000320193-26-000001"],
                    "filingDate": ["2026-08-01", "2026-08-02"],
                    "reportDate": [""],
                    "form": ["10-K"],
                    "primaryDocument": ["x.htm"],
                }
            },
        }
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "submissions/CIK": submissions})
        provider = SecEdgarFilingHistoryProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_non_dict_response_raises_malformed(self):
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "submissions/CIK": ["not", "a", "dict"]})
        provider = SecEdgarFilingHistoryProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_content_hash_differs_for_different_accessions(self):
        fetcher = _fake_fetcher(
            {"company_tickers.json": _TICKER_MAP, "submissions/CIK": _REAL_SHAPE_SUBMISSIONS}
        )
        provider = SecEdgarFilingHistoryProvider(fetcher)
        documents = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        hashes = {d.content_hash for d in documents}
        assert len(hashes) == len(documents)

    def test_identity_cache_is_reused_across_calls_within_one_provider(self):
        """Confirms `SecEdgarIdentity`'s own cache is genuinely reused
        -- the ticker map is fetched exactly once even though two
        separate `fetch()` calls each need CIK resolution."""
        call_count = {"ticker_map": 0}

        def counting_fetcher(url: str, headers: dict | None) -> object:
            if "company_tickers.json" in url:
                call_count["ticker_map"] += 1
                return _TICKER_MAP
            if "submissions/CIK" in url:
                return _REAL_SHAPE_SUBMISSIONS
            raise AssertionError(f"unexpected URL: {url}")

        provider = SecEdgarFilingHistoryProvider(counting_fetcher)
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert call_count["ticker_map"] == 1
