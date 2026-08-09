"""Alpha Vantage market-data provider contract tests (ATLAS-031, Phase
33). All fake -- no live network anywhere in this file.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.errors import (
    CompanyNotFound,
    MalformedProviderResponse,
    MissingRequiredField,
    RateLimited,
    UnsupportedUnit,
)

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)


def _fake_fetcher(responses: dict[str, object]):
    def fetcher(url: str, headers: dict | None) -> object:
        for key, value in responses.items():
            if key in url:
                return value
        raise AssertionError(f"unexpected URL in test: {url}")

    return fetcher


class TestMissingApiKey:
    def test_missing_api_key_raises_missing_required_field(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        provider = AlphaVantageMarketDataProvider(lambda url, headers: {})
        with pytest.raises(MissingRequiredField):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_explicit_api_key_overrides_environment(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "env-key")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "SharesOutstanding": "1000000", "Currency": "USD"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, api_key="explicit-key")
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1


class TestProviderErrorShapes:
    """Alpha Vantage returns HTTP 200 for its own error states -- this
    is the one place that shape gets translated into typed errors."""

    def test_error_message_shape_raises_company_not_found(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Error Message": "Invalid API call"}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(CompanyNotFound):
            provider.fetch(company_identifier="ZZZZ", evaluated_at=_NOW)

    def test_note_shape_raises_rate_limited(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Note": "Thank you for using Alpha Vantage! ... call frequency"}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(RateLimited):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_information_shape_raises_rate_limited(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Information": "demo key restricted"}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(RateLimited):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_empty_global_quote_raises_company_not_found(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Global Quote": {}}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(CompanyNotFound):
            provider.fetch(company_identifier="ZZZZ", evaluated_at=_NOW)

    def test_malformed_response_shape_raises_malformed(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": ["not", "a", "dict"]})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_missing_price_or_trading_day_raises_malformed(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00"}}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)


class TestCurrencySafety:
    def test_non_usd_currency_raises_unsupported_unit(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "VOLV-B", "SharesOutstanding": "2000000", "Currency": "SEK"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(UnsupportedUnit):
            provider.fetch(company_identifier="VOLV-B", evaluated_at=_NOW)


class TestPartialCoverage:
    def test_missing_shares_outstanding_still_produces_price_only_document(self, monkeypatch):
        """OVERVIEW momentarily unavailable/empty -- the fetch is not
        aborted; the downstream Valuation evaluator reports its own
        honest INSUFFICIENT_INPUT for that gap (Phase 9's own explicit
        instruction)."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert doc.metadata["share_price"] == 150.00
        assert "shares_outstanding" not in doc.metadata


class TestDocumentShape:
    def test_document_is_a_single_market_data_snapshot_with_both_facts(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "191.55", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "SharesOutstanding": "14840000000", "Currency": "USD"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1
        (doc,) = docs
        assert isinstance(doc, RawBusinessDocument)
        assert doc.source_kind == "market_data_snapshot"
        assert doc.provider_id == "alpha_vantage"
        assert doc.metadata["share_price"] == 191.55
        assert doc.metadata["shares_outstanding"] == 14840000000.0
        assert doc.metadata["currency"] == "USD"
        assert doc.period_end.isoformat() == "2026-08-07"
        assert doc.identifier == "AAPL:snapshot:2026-08-07"

    def test_deterministic_content_hash_for_identical_snapshot(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "SharesOutstanding": "1000000", "Currency": "USD"},
            }
        )
        docs_a = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        docs_b = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs_a[0].content_hash == docs_b[0].content_hash

    def test_price_change_produces_a_different_content_hash(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher_a = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "SharesOutstanding": "1000000", "Currency": "USD"},
            }
        )
        fetcher_b = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "155.00", "07. latest trading day": "2026-08-08"}},
                "OVERVIEW": {"Symbol": "AAPL", "SharesOutstanding": "1000000", "Currency": "USD"},
            }
        )
        doc_a = AlphaVantageMarketDataProvider(fetcher_a).fetch(company_identifier="AAPL", evaluated_at=_NOW)[0]
        doc_b = AlphaVantageMarketDataProvider(fetcher_b).fetch(company_identifier="AAPL", evaluated_at=_NOW)[0]
        assert doc_a.content_hash != doc_b.content_hash
