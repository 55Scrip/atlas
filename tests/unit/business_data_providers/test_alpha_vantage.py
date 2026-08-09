"""Alpha Vantage market-data provider contract tests (ATLAS-031, Phase
33; ATLAS-031B adds the inter-request delay tests). All fake -- no live
network anywhere in this file.
"""
from __future__ import annotations

import time
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


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch):
    """ATLAS-031B: `AlphaVantageMarketDataProvider` now pauses between
    `GLOBAL_QUOTE` and `OVERVIEW` by default (`time.sleep`, resolved
    fresh per call -- see the provider's own docstring on why). Patched
    globally here so every test in this file stays fast without having
    to inject a fake sleeper into each individual construction; tests
    that specifically assert the delay's own call order/count/args
    inject an explicit fake sleeper instead and are unaffected by this
    patch (their own explicit sleeper always wins)."""
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


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
    def test_missing_shares_outstanding_with_confirmed_currency_still_reports_price(self, monkeypatch):
        """Currency IS confirmed (USD) but OVERVIEW genuinely lacks
        SharesOutstanding -- the fetch is not aborted; share_price is
        still reported (its own denomination is known), and the
        downstream Valuation evaluator reports its own honest
        INSUFFICIENT_INPUT for the missing share count (Phase 9's own
        explicit instruction)."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert doc.metadata["share_price"] == 150.00
        assert doc.metadata["currency"] == "USD"
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


class TestCurrencySafety:
    """ATLAS-031A, Issue 1 -- the post-sprint audit found (and this
    file reproduced live) that an empty `OVERVIEW` caused the provider
    to silently report `currency: "USD"` with no actual confirmation,
    a real "mathematically valid, economically meaningless" risk. This
    class proves the corrected behavior: currency is never assumed,
    only ever confirmed."""

    def test_empty_overview_produces_no_share_price_or_currency(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "285.50", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {},
            }
        )
        (doc,) = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="VOLV-B", evaluated_at=_NOW)
        assert "share_price" not in doc.metadata
        assert "currency" not in doc.metadata
        assert "shares_outstanding" not in doc.metadata

    def test_overview_present_but_missing_currency_field_produces_no_share_price(self, monkeypatch):
        """OVERVIEW returns real data (e.g. a real SharesOutstanding)
        but genuinely omits the Currency field -- still not enough to
        assume USD."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "285.50", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "VOLV-B", "SharesOutstanding": "2000000000"},
            }
        )
        (doc,) = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="VOLV-B", evaluated_at=_NOW)
        assert "share_price" not in doc.metadata
        assert "currency" not in doc.metadata
        assert "shares_outstanding" not in doc.metadata

    def test_blank_currency_string_is_treated_as_unconfirmed_not_usd(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "  "},
            }
        )
        (doc,) = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "share_price" not in doc.metadata
        assert "currency" not in doc.metadata

    def test_unknown_currency_never_silently_becomes_usd(self, monkeypatch):
        """The exact regression this issue exists to prevent: no code
        path may produce `metadata["currency"] == "USD"` unless a real
        OVERVIEW response actually said so."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "99.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {},
            }
        )
        (doc,) = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="XYZ", evaluated_at=_NOW)
        assert doc.metadata.get("currency") != "USD"
        assert "currency" not in doc.metadata

    def test_missing_currency_and_share_price_yields_no_valuation_fact(self, monkeypatch):
        """End-to-end proof, not just a metadata check: run the
        resulting document through the real, unmodified
        `extract_valuation_facts` and confirm zero facts come out --
        "no valuation produced," per the audit's own wording."""
        from atlas.analysis_engine.business_data.contracts import ValidationStatus
        from atlas.analysis_engine.business_data.models import BusinessRecord, RecordVersion
        from atlas.analysis_engine.business_data.sources import SourceKind as DocumentSourceKind
        from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
        from atlas.analysis_engine.valuation.facts import extract_valuation_facts

        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "285.50", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {},
            }
        )
        (raw_doc,) = AlphaVantageMarketDataProvider(fetcher).fetch(company_identifier="VOLV-B", evaluated_at=_NOW)

        record = BusinessRecord(
            id="lineage:v1",
            lineage_id="lineage",
            identifier=raw_doc.identifier,
            company=raw_doc.company,
            document_type=DocumentSourceKind(raw_doc.source_kind),
            published_at=raw_doc.published_at,
            provider_id=raw_doc.provider_id,
            source_reference=raw_doc.raw_reference,
            content_hash=raw_doc.content_hash,
            version=RecordVersion(version_number=1, created_at=_NOW, content_hash=raw_doc.content_hash),
            provenance=Provenance(
                source_kind=SourceKind.EXTERNAL_DATA_SOURCE,
                source_references=(raw_doc.raw_reference,),
                dependencies=(),
                update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
                consumers=(Consumer.PORTFOLIO_PAGE,),
                computed_at=_NOW,
            ),
            validation_status=ValidationStatus.VALID,
            period_start=raw_doc.period_start,
            period_end=raw_doc.period_end,
            language=raw_doc.language,
            metadata=raw_doc.metadata,
        )
        facts = extract_valuation_facts(record, evaluated_at=_NOW)
        assert facts == ()


class TestInterRequestDelay:
    """ATLAS-031B -- live testing with a real key found Alpha Vantage's
    free tier rejects a second call made less than ~1 second after the
    first. These tests use an explicit fake sleeper (never the real
    `time.sleep`, even with the autouse patch active) so the delay's
    own call order, count, and argument can be asserted precisely."""

    def test_global_quote_is_called_before_overview(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_order: list[str] = []

        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                call_order.append("GLOBAL_QUOTE")
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            call_order.append("OVERVIEW")
            return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}

        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: call_order.append("SLEEP"))
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert call_order == ["GLOBAL_QUOTE", "SLEEP", "OVERVIEW"]

    def test_delay_is_invoked_exactly_once_with_the_configured_seconds(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )
        sleep_calls: list[float] = []
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=1.1)
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == [1.1]

    def test_default_sleeper_is_time_sleep_and_test_suite_never_actually_waits(self, monkeypatch):
        """No explicit sleeper injected -- exercises the real default
        path (`time.sleep`, resolved fresh at call time), relying only
        on this file's autouse `_no_real_sleep` patch to keep it fast.
        Elapsed wall-clock time stays far below the configured 1.1s."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        started = time.monotonic()
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert time.monotonic() - started < 1.0

    def test_valid_market_data_extraction_still_works_with_the_delay_in_place(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "191.55", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "14840000000"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert doc.metadata["share_price"] == 191.55
        assert doc.metadata["shares_outstanding"] == 14840000000.0
        assert doc.metadata["currency"] == "USD"

    def test_missing_currency_behavior_unchanged_with_the_delay_in_place(self, monkeypatch):
        """ATLAS-031A's currency-safety fix must survive unchanged."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "share_price" not in doc.metadata
        assert "currency" not in doc.metadata

    def test_explicit_non_usd_currency_still_unsupported_with_the_delay_in_place(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "285.50", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "VOLV-B", "Currency": "SEK"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        with pytest.raises(UnsupportedUnit):
            provider.fetch(company_identifier="VOLV-B", evaluated_at=_NOW)

    def test_rate_limit_on_the_second_call_still_surfaces_as_rate_limited(self, monkeypatch):
        """A rate-limit response on OVERVIEW (the call made *after* the
        delay) must still raise the existing typed error -- the delay
        must never swallow or mask a provider-level failure."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Note": "Thank you for using Alpha Vantage! ... call frequency"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        with pytest.raises(RateLimited):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_api_key_never_appears_in_raw_reference(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "super-secret-key-value")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "super-secret-key-value" not in doc.raw_reference

    def test_api_key_never_appears_in_error_text(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "super-secret-key-value")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Error Message": "Invalid API call"}})
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        with pytest.raises(CompanyNotFound) as excinfo:
            provider.fetch(company_identifier="ZZZZ", evaluated_at=_NOW)
        assert "super-secret-key-value" not in str(excinfo.value)
