"""Alpha Vantage market-data provider contract tests (ATLAS-031, Phase
33; ATLAS-031B adds the inter-request delay tests). All fake -- no live
network anywhere in this file.
"""
from __future__ import annotations

import time
from datetime import date as date_
from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.business_data_providers.alpha_vantage import (
    _DEFAULT_INTER_REQUEST_DELAY_SECONDS,
    AlphaVantageMarketDataProvider,
)
from atlas.business_data_providers.errors import (
    NoIdentityDataForSymbol,
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


class _FakeClock:
    """A deterministic, controllable monotonic clock (ATLAS-032
    corrective) -- starts at `0.0` and only advances when `advance()`
    is called explicitly, so pacing tests can assert exact remaining-
    interval math instead of tolerating real wall-clock jitter."""

    def __init__(self) -> None:
        self._now = 0.0

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


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
        """A fixed (never-advancing) fake clock means zero real time
        elapses between the two requests inside `fetch()`, so the
        pacing math (`_inter_request_delay_seconds - elapsed`) must
        sleep the exact configured delay -- proves the "remaining
        interval" calculation degrades correctly to a flat delay when
        elapsed time is genuinely zero."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )
        sleep_calls: list[float] = []
        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=1.1, clock=_FakeClock()
        )
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


class TestInstanceLevelPacing:
    """ATLAS-032 corrective -- live testing found the real per-second
    spacing defect was NOT within `fetch()` or `fetch_historical_snapshots()`
    individually (both already paced their own internal calls
    correctly), but at the *boundary* between the two: `fetch()`'s own
    `OVERVIEW` call and `fetch_historical_snapshots()`'s own `OVERVIEW`
    call were separated by zero sleep, because each method only paced
    calls it made itself and neither had any awareness the other had
    just run on the same instance. These tests exercise the invariant
    directly -- no outbound Alpha Vantage request may begin less than
    `_inter_request_delay_seconds` after the preceding one this
    instance made, regardless of which public method triggered either
    one -- rather than re-testing internals already covered elsewhere.
    """

    def test_first_request_on_a_fresh_instance_never_sleeps(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        fetcher = _fake_fetcher(
            {
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
                "TIME_SERIES_MONTHLY_ADJUSTED": {
                    "Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}
                },
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=sleep_calls.append, clock=_FakeClock())
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        # Two real AV requests happen here (OVERVIEW, then
        # TIME_SERIES_MONTHLY_ADJUSTED) -- exactly one sleep should
        # occur (before the second), proving the very first request a
        # freshly constructed instance ever makes is never delayed.
        #
        # No `inter_request_delay_seconds` is injected here on purpose:
        # this is the one pacing test that exercises the real default,
        # so it asserts against the constant rather than a literal. The
        # claim under test is "exactly one sleep, and not before the
        # first request" -- the magnitude is whatever production ships.
        assert sleep_calls == [_DEFAULT_INTER_REQUEST_DELAY_SECONDS]

    def test_fetch_then_fetch_historical_snapshots_paces_across_the_method_boundary(self, monkeypatch):
        """The exact regression this corrective fix targets: calling
        `fetch()` and then `fetch_historical_snapshots()` on the SAME
        provider instance -- exactly how `refresh_company_data` uses
        it, in two separate loops -- must still pace correctly across
        the method boundary. ATLAS-033 additionally eliminates the
        second `OVERVIEW` call entirely (reused from `fetch()`'s own
        already-parsed result), so the real sequence is `GLOBAL_QUOTE,
        OVERVIEW, TIME_SERIES_MONTHLY_ADJUSTED` -- pacing still applies
        between each *real* request, never before a reused one."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_order: list[str] = []

        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                call_order.append("GLOBAL_QUOTE")
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            if "OVERVIEW" in url:
                call_order.append("OVERVIEW")
                return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}
            call_order.append("TIME_SERIES_MONTHLY_ADJUSTED")
            return {"Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}}

        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=lambda seconds: call_order.append("SLEEP"), clock=_FakeClock()
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        # Ingestion/database work happens here in the real orchestrator
        # (refresh_company_data) between the two public-method calls --
        # simulated here by simply calling straight through, the worst
        # case for pacing since the fixed fake clock advances zero
        # real time on its own.
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert call_order == [
            "GLOBAL_QUOTE",
            "SLEEP",
            "OVERVIEW",
            "SLEEP",  # still paces the next REAL request -- OVERVIEW itself is reused, not repeated
            "TIME_SERIES_MONTHLY_ADJUSTED",
        ]
        assert call_order.count("OVERVIEW") == 1

    def test_consecutive_requests_inside_fetch_respect_the_minimum_interval(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )
        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=1.1, clock=_FakeClock()
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == [1.1]

    def test_consecutive_requests_inside_fetch_historical_snapshots_respect_the_minimum_interval(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        fetcher = _fake_fetcher(
            {
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
                "TIME_SERIES_MONTHLY_ADJUSTED": {
                    "Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}
                },
            }
        )
        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=1.1, clock=_FakeClock()
        )
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert sleep_calls == [1.1]

    def test_only_the_remaining_interval_is_slept_when_time_has_already_elapsed(self, monkeypatch):
        """If real (or, here, fake) time already advanced between two
        requests, pacing must sleep only the shortfall -- never a flat
        `_inter_request_delay_seconds` regardless of elapsed time."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        clock = _FakeClock()

        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                # Simulate 0.4s of real elapsed time (e.g. genuine
                # network latency) between the two requests inside fetch().
                clock.advance(0.4)
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}

        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=1.1, clock=clock
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == [pytest.approx(0.7)]

    def test_no_sleep_at_all_when_the_full_interval_has_already_elapsed(self, monkeypatch):
        """If at least `_inter_request_delay_seconds` has already
        genuinely passed since the last request, the next request must
        not sleep at all."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        clock = _FakeClock()

        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                clock.advance(2.0)  # far more than the 1.1s configured delay
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}

        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=1.1, clock=clock
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == []

    def test_request_order_and_document_content_are_unaffected_by_the_pacing_change(self, monkeypatch):
        """The pacing rewrite touches only when calls happen, never
        what they return -- a full end-to-end fetch() +
        fetch_historical_snapshots() pair still produces the exact
        same document shape and values as before."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "191.55", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "14840000000"},
                "TIME_SERIES_MONTHLY_ADJUSTED": {
                    "Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}
                },
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None, clock=_FakeClock())
        (current_doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert current_doc.metadata["share_price"] == 191.55
        assert current_doc.metadata["shares_outstanding"] == 14840000000.0
        assert current_doc.metadata["currency"] == "USD"

        (historical_doc,) = provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert historical_doc.metadata["share_price"] == 40.00
        assert historical_doc.metadata["shares_outstanding"] == 14840000000.0
        assert historical_doc.period_start == date_(2023, 2, 28)


def _monthly_fetcher(series: dict[str, dict], *, overview: dict | None = None):
    responses = {
        "TIME_SERIES_MONTHLY_ADJUSTED": {"Monthly Adjusted Time Series": series},
        "OVERVIEW": overview if overview is not None else {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
    }
    return _fake_fetcher(responses)


class TestHistoricalSnapshots:
    """ATLAS-032, Phase 7 -- `fetch_historical_snapshots`, the
    split-adjusted-monthly-close, no-look-ahead sampling path."""

    def test_no_filing_dates_makes_no_api_call_at_all(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")

        def fetcher(url: str, headers):
            raise AssertionError("no API call should happen for an empty filing_dates tuple")

        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        docs = provider.fetch_historical_snapshots(company_identifier="AAPL", filing_dates=(), evaluated_at=_NOW)
        assert docs == ()

    def test_single_filing_date_samples_first_close_on_or_after(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher(
            {
                "2022-12-30": {"4. close": "30.00", "5. adjusted close": "30.00"},
                "2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"},
                "2023-03-31": {"4. close": "42.00", "5. adjusted close": "42.00"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 15),), evaluated_at=_NOW
        )
        # 2023-02-28 is the first monthly close on or after 2023-02-15
        # -- never 2022-12-30 (before the filing) or 2023-03-31 (a
        # later, non-nearest candidate).
        assert doc.period_start == date_(2023, 2, 28)
        assert doc.metadata["share_price"] == 40.00
        assert doc.metadata["shares_outstanding"] == 1000000.0
        assert doc.metadata["currency"] == "USD"
        assert doc.source_kind == "market_data_snapshot"

    def test_no_close_after_a_filing_date_produces_no_document_for_it(self, monkeypatch):
        """A filing date newer than every available monthly close is
        silently skipped -- never fabricated forward to a nearest or
        most-recent price."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher({"2020-01-31": {"4. close": "10.00", "5. adjusted close": "10.00"}})
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        docs = provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2025, 1, 1),), evaluated_at=_NOW
        )
        assert docs == ()

    def test_multiple_filing_dates_mapping_to_the_same_close_collapse_to_one_document(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher({"2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"}})
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        docs = provider.fetch_historical_snapshots(
            company_identifier="AAPL",
            filing_dates=(date_(2023, 2, 1), date_(2023, 2, 15), date_(2023, 2, 20)),
            evaluated_at=_NOW,
        )
        assert len(docs) == 1
        assert docs[0].period_start == date_(2023, 2, 28)

    def test_distinct_filing_dates_produce_distinct_sorted_documents(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher(
            {
                "2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"},
                "2024-02-29": {"4. close": "45.00", "5. adjusted close": "45.00"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        docs = provider.fetch_historical_snapshots(
            company_identifier="AAPL",
            filing_dates=(date_(2024, 2, 1), date_(2023, 2, 1)),  # deliberately out of order
            evaluated_at=_NOW,
        )
        assert [d.period_start for d in docs] == [date_(2023, 2, 28), date_(2024, 2, 29)]

    def test_published_at_is_the_sampled_trading_date_not_evaluated_at(self, monkeypatch):
        """A historical close was genuinely public on its own trading
        day -- unlike the current snapshot, this must not collapse to
        `evaluated_at` (when Atlas happened to fetch it)."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher({"2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"}})
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert doc.published_at.date() == date_(2023, 2, 28)
        assert doc.published_at != _NOW

    def test_unconfirmed_currency_omits_price_entirely(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher(
            {"2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"}}, overview={}
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert "share_price" not in doc.metadata
        assert "currency" not in doc.metadata

    def test_explicit_non_usd_currency_raises_unsupported_unit(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher(
            {"2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"}},
            overview={"Symbol": "VOLV-B", "Currency": "SEK"},
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        with pytest.raises(UnsupportedUnit):
            provider.fetch_historical_snapshots(
                company_identifier="VOLV-B", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
            )

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        provider = AlphaVantageMarketDataProvider(lambda url, headers: {}, sleeper=lambda seconds: None)
        with pytest.raises(MissingRequiredField):
            provider.fetch_historical_snapshots(
                company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
            )

    def test_malformed_series_response_raises(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"TIME_SERIES_MONTHLY_ADJUSTED": {"unexpected": "shape"}, "OVERVIEW": {}})
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch_historical_snapshots(
                company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
            )

    def test_rate_limit_on_the_monthly_call_surfaces_as_rate_limited(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "TIME_SERIES_MONTHLY_ADJUSTED": {"Note": "Thank you for using Alpha Vantage! ... call frequency"},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD"},
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        with pytest.raises(RateLimited):
            provider.fetch_historical_snapshots(
                company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
            )

    def test_paced_overview_then_monthly_series_in_order(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_order: list[str] = []

        def fetcher(url: str, headers):
            if "OVERVIEW" in url:
                call_order.append("OVERVIEW")
                return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}
            call_order.append("TIME_SERIES_MONTHLY_ADJUSTED")
            return {"Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}}

        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: call_order.append("SLEEP"))
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert call_order == ["OVERVIEW", "SLEEP", "TIME_SERIES_MONTHLY_ADJUSTED"]

    def test_no_real_wait_for_the_default_sleeper(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _monthly_fetcher({"2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        started = time.monotonic()
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert time.monotonic() - started < 1.0

    def test_api_key_never_appears_in_raw_reference(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "super-secret-key-value")
        fetcher = _monthly_fetcher({"2023-02-28": {"4. close": "40.00", "5. adjusted close": "40.00"}})
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc,) = provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert "super-secret-key-value" not in doc.raw_reference


class TestOverviewDeduplication:
    """ATLAS-033 -- `fetch()` and `fetch_historical_snapshots()` on the
    same provider instance must issue at most one real `OVERVIEW`
    request between them, reusing the already-parsed
    `SharesOutstanding`/`Currency` values rather than re-fetching
    identical current-basis data."""

    @staticmethod
    def _counting_fetcher(call_counts: dict[str, int]):
        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                call_counts["GLOBAL_QUOTE"] = call_counts.get("GLOBAL_QUOTE", 0) + 1
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            if "OVERVIEW" in url:
                call_counts["OVERVIEW"] = call_counts.get("OVERVIEW", 0) + 1
                return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}
            call_counts["TIME_SERIES_MONTHLY_ADJUSTED"] = call_counts.get("TIME_SERIES_MONTHLY_ADJUSTED", 0) + 1
            return {"Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}}

        return fetcher

    def test_fetch_then_fetch_historical_snapshots_makes_only_one_overview_request(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_counts: dict[str, int] = {}
        provider = AlphaVantageMarketDataProvider(
            self._counting_fetcher(call_counts), sleeper=lambda seconds: None
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert call_counts["OVERVIEW"] == 1
        assert call_counts["GLOBAL_QUOTE"] == 1
        assert call_counts["TIME_SERIES_MONTHLY_ADJUSTED"] == 1

    def test_fetch_historical_snapshots_called_first_still_makes_its_own_overview_request(self, monkeypatch):
        """No prior `fetch()` on this instance -- the cache is empty,
        so `fetch_historical_snapshots` must still make a real
        `OVERVIEW` request itself, exactly as before this optimization."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_counts: dict[str, int] = {}
        provider = AlphaVantageMarketDataProvider(
            self._counting_fetcher(call_counts), sleeper=lambda seconds: None
        )
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert call_counts["OVERVIEW"] == 1
        assert "GLOBAL_QUOTE" not in call_counts

    def test_a_second_fetch_historical_snapshots_call_reuses_the_same_cached_overview(self, monkeypatch):
        """Reuse is not a one-shot: once populated (by either method),
        every subsequent call on this instance for the same ticker
        keeps reusing it, never re-fetching."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_counts: dict[str, int] = {}
        provider = AlphaVantageMarketDataProvider(
            self._counting_fetcher(call_counts), sleeper=lambda seconds: None
        )
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2024, 2, 1),), evaluated_at=_NOW
        )
        assert call_counts["OVERVIEW"] == 1

    def test_a_different_ticker_still_makes_its_own_overview_request(self, monkeypatch):
        """The cache is ticker-scoped -- reusing AAPL's OVERVIEW data
        for MSFT would silently report the wrong company's shares
        outstanding and currency, so a different ticker must always
        trigger a fresh real request."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_counts: dict[str, int] = {}
        provider = AlphaVantageMarketDataProvider(
            self._counting_fetcher(call_counts), sleeper=lambda seconds: None
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        provider.fetch_historical_snapshots(
            company_identifier="MSFT", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert call_counts["OVERVIEW"] == 2

    def test_historical_documents_are_byte_for_byte_identical_with_or_without_a_prior_fetch(self, monkeypatch):
        """The optimization must be invisible to callers: the exact
        same historical document (metadata, content_hash, identifier,
        dates) is produced whether or not `fetch()` ran first."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")

        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            if "OVERVIEW" in url:
                return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}
            return {"Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}}

        provider_with_prior_fetch = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        provider_with_prior_fetch.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        (doc_reused,) = provider_with_prior_fetch.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )

        provider_standalone = AlphaVantageMarketDataProvider(fetcher, sleeper=lambda seconds: None)
        (doc_fresh,) = provider_standalone.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )

        assert doc_reused == doc_fresh


class TestFetchCompanyProfile:
    """(Investment Case Engine v1 slice) `fetch_company_profile` --
    reuses the same cached OVERVIEW response `fetch`/`fetch_historical_
    snapshots` already use; no network call of its own is asserted
    directly (the fetcher raises `AssertionError` on any unexpected
    URL, so a redundant OVERVIEW request would already fail these
    tests)."""

    def test_returns_one_company_profile_document_with_identity_fields(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "OVERVIEW": {
                    "Symbol": "AAPL",
                    "Name": "Apple Inc.",
                    "Exchange": "NASDAQ",
                    "Sector": "TECHNOLOGY",
                    "Industry": "CONSUMER ELECTRONICS",
                    "Country": "USA",
                    "Description": "Apple Inc. designs, manufactures, and markets smartphones.",
                    "SharesOutstanding": "14840000000",
                    "Currency": "USD",
                    "FiscalYearEnd": "September",
                }
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        docs = provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1
        (doc,) = docs
        assert doc.source_kind == "company_profile"
        assert doc.provider_id == "alpha_vantage"
        assert doc.company == "AAPL"
        assert doc.metadata["name"] == "Apple Inc."
        assert doc.metadata["exchange"] == "NASDAQ"
        assert doc.metadata["sector"] == "TECHNOLOGY"
        assert doc.metadata["industry"] == "CONSUMER ELECTRONICS"
        assert doc.metadata["country"] == "USA"
        assert "smartphones" in doc.metadata["description"]
        assert doc.metadata["currency"] == "USD"
        assert doc.metadata["fiscal_year_end"] == "September"

    def test_asset_type_is_extracted_into_metadata(self, monkeypatch):
        """Sprint O.1 -- `AssetType` is a real field in Alpha Vantage's
        OVERVIEW response (confirmed via the sprint's own live
        documentation verification), extracted the same way every other
        identity field already is: verbatim, untranslated, under the
        `asset_type` metadata key."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "OVERVIEW": {
                    "Symbol": "AAPL",
                    "Name": "Apple Inc.",
                    "AssetType": "Common Stock",
                    "Exchange": "NASDAQ",
                    "Country": "USA",
                    "Currency": "USD",
                }
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        (doc,) = provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)
        assert doc.metadata["asset_type"] == "Common Stock"

    def test_literal_none_string_asset_type_is_omitted_not_stored(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"OVERVIEW": {"Symbol": "XYZ", "Name": "Xyz Corp", "AssetType": "None"}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        (doc,) = provider.fetch_company_profile(company_identifier="XYZ", evaluated_at=_NOW)
        assert "asset_type" not in doc.metadata

    def test_literal_none_string_fields_are_omitted_not_stored(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {
                "OVERVIEW": {
                    "Symbol": "XYZ",
                    "Name": "Xyz Corp",
                    "Sector": "None",
                    "Industry": "None",
                    "Currency": "None",
                    "FiscalYearEnd": "None",
                }
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        (doc,) = provider.fetch_company_profile(company_identifier="XYZ", evaluated_at=_NOW)
        assert doc.metadata["name"] == "Xyz Corp"
        assert "sector" not in doc.metadata
        assert "industry" not in doc.metadata
        assert "currency" not in doc.metadata
        assert "fiscal_year_end" not in doc.metadata

    def test_currency_and_fiscal_year_end_are_optional(self, monkeypatch):
        """Company Data Foundation v1: a ticker whose OVERVIEW response
        carries other identity fields but not these two still produces
        a real profile document -- never blocked by their absence."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"OVERVIEW": {"Symbol": "XYZ", "Name": "Xyz Corp"}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        (doc,) = provider.fetch_company_profile(company_identifier="XYZ", evaluated_at=_NOW)
        assert doc.metadata["name"] == "Xyz Corp"
        assert "currency" not in doc.metadata
        assert "fiscal_year_end" not in doc.metadata

    def test_empty_overview_raises_no_identity_data_for_symbol(self, monkeypatch):
        """Changed 2026-09-02. This previously asserted `docs == ()`,
        which made "the provider answered and had nothing" indistinguishable
        from "never asked" -- Atlas then told the investor identity had
        failed for a retryable reason, which was false. See
        `NoIdentityDataForSymbol`."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"OVERVIEW": {}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(NoIdentityDataForSymbol):
            provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        provider = AlphaVantageMarketDataProvider(_fake_fetcher({}))
        with pytest.raises(MissingRequiredField):
            provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)

    def test_calling_fetch_then_fetch_company_profile_makes_only_one_overview_request(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_count = {"OVERVIEW": 0, "GLOBAL_QUOTE": 0}

        def fetcher(url: str, headers) -> object:
            if "GLOBAL_QUOTE" in url:
                call_count["GLOBAL_QUOTE"] += 1
                return {"Global Quote": {"05. price": "191.55", "07. latest trading day": "2026-08-07"}}
            if "OVERVIEW" in url:
                call_count["OVERVIEW"] += 1
                return {"Symbol": "AAPL", "Name": "Apple Inc.", "SharesOutstanding": "100", "Currency": "USD"}
            raise AssertionError(f"unexpected URL: {url}")

        provider = AlphaVantageMarketDataProvider(fetcher)
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        profile_docs = provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)

        assert call_count["OVERVIEW"] == 1  # cached from `fetch`, never requested a second time
        assert len(profile_docs) == 1
        assert profile_docs[0].metadata["name"] == "Apple Inc."

    def test_calling_fetch_company_profile_first_still_populates_the_shared_cache(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_count = {"OVERVIEW": 0, "GLOBAL_QUOTE": 0}

        def fetcher(url: str, headers) -> object:
            if "GLOBAL_QUOTE" in url:
                call_count["GLOBAL_QUOTE"] += 1
                return {"Global Quote": {"05. price": "191.55", "07. latest trading day": "2026-08-07"}}
            if "OVERVIEW" in url:
                call_count["OVERVIEW"] += 1
                return {"Symbol": "AAPL", "Name": "Apple Inc.", "SharesOutstanding": "100", "Currency": "USD"}
            raise AssertionError(f"unexpected URL: {url}")

        provider = AlphaVantageMarketDataProvider(fetcher)
        provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

        assert call_count["OVERVIEW"] == 1
        assert doc.metadata["shares_outstanding"] == 100.0

    def test_a_different_ticker_still_makes_its_own_overview_request(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_count = {"OVERVIEW": 0}

        def fetcher(url: str, headers) -> object:
            call_count["OVERVIEW"] += 1
            symbol = "AAPL" if "symbol=AAPL" in url else "MSFT"
            return {"Symbol": symbol, "Name": f"{symbol} Inc.", "Currency": "USD"}

        provider = AlphaVantageMarketDataProvider(fetcher)
        provider.fetch_company_profile(company_identifier="AAPL", evaluated_at=_NOW)
        provider.fetch_company_profile(company_identifier="MSFT", evaluated_at=_NOW)
        assert call_count["OVERVIEW"] == 2


def _transcript_fetcher(entries: list[dict]):
    return _fake_fetcher({"EARNINGS_CALL_TRANSCRIPT": {"symbol": "AAPL", "quarter": "2026Q2", "transcript": entries}})


class TestEarningsCallTranscripts:
    """Capability Expansion Sprint 2 -- `fetch_earnings_call_transcripts`,
    the most-recently-ended-calendar-quarter, one-document-per-statement
    path. `_NOW` is 2026-08-09, so the most recently ended calendar
    quarter is `2026Q2` (Apr-Jun)."""

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        provider = AlphaVantageMarketDataProvider(lambda url, headers: {})
        with pytest.raises(MissingRequiredField):
            provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)

    def test_requests_the_most_recently_ended_calendar_quarter(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        seen_urls = []

        def fetcher(url: str, headers):
            seen_urls.append(url)
            return {"symbol": "AAPL", "quarter": "2026Q2", "transcript": []}

        provider = AlphaVantageMarketDataProvider(fetcher)
        provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)
        assert any("quarter=2026Q2" in url for url in seen_urls)

    def test_an_empty_transcript_produces_no_documents(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        provider = AlphaVantageMarketDataProvider(_transcript_fetcher([]))
        docs = provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs == ()

    def test_one_document_per_statement(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        entries = [
            {"speaker": "Operator", "title": "", "content": "Good afternoon, welcome.", "sentiment": "0.1"},
            {"speaker": "Tim Cook", "title": "CEO", "content": "Thank you, we had a strong quarter.", "sentiment": "0.7"},
        ]
        provider = AlphaVantageMarketDataProvider(_transcript_fetcher(entries))
        docs = provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 2
        assert docs[0].metadata["speaker"] == "Operator"
        assert docs[0].metadata["statement_index"] == 0
        assert "title" not in docs[0].metadata  # empty title omitted, never persisted as blank
        assert docs[1].metadata["speaker"] == "Tim Cook"
        assert docs[1].metadata["title"] == "CEO"
        assert docs[1].metadata["sentiment"] == 0.7
        assert docs[1].metadata["quarter"] == "2026Q2"
        assert docs[1].source_kind == "transcript"
        assert docs[1].identifier == "AAPL:transcript:2026Q2:1"
        assert docs[1].period_end == date_(2026, 6, 30)

    def test_a_statement_with_no_sentiment_reported_omits_the_field(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        entries = [{"speaker": "CFO", "title": "CFO", "content": "Revenue grew 8%."}]
        provider = AlphaVantageMarketDataProvider(_transcript_fetcher(entries))
        (doc,) = provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)
        assert "sentiment" not in doc.metadata

    def test_a_malformed_entry_missing_content_is_skipped(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        entries = [{"speaker": "CFO", "content": ""}, {"speaker": "CEO", "content": "Real statement."}]
        provider = AlphaVantageMarketDataProvider(_transcript_fetcher(entries))
        docs = provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["content"] == "Real statement."

    def test_published_at_is_evaluated_at(self, monkeypatch):
        """Unlike historical price snapshots, the true call date is not
        reliably known from this endpoint -- `evaluated_at` (when Atlas
        fetched it) is the honest choice, mirroring `fetch()`'s own
        current-snapshot precedent."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        entries = [{"speaker": "CEO", "content": "Statement."}]
        provider = AlphaVantageMarketDataProvider(_transcript_fetcher(entries))
        (doc,) = provider.fetch_earnings_call_transcripts(company_identifier="AAPL", evaluated_at=_NOW)
        assert doc.published_at == _NOW


def _counting_fetcher(responses: dict[str, object]):
    """Like `_fake_fetcher`, but also records every URL actually
    requested -- `fetch_price_only`'s whole point is costing exactly
    one real call, so its own tests assert the real count, not just
    the returned document's shape."""
    calls: list[str] = []

    def fetcher(url: str, headers: dict | None) -> object:
        calls.append(url)
        for key, value in responses.items():
            if key in url:
                return value
        raise AssertionError(f"unexpected URL in test: {url}")

    fetcher.calls = calls  # type: ignore[attr-defined]
    return fetcher


class TestFetchPriceOnly:
    """Internal Alpha Stabilization 1 (MSFT price root cause fix):
    `fetch_price_only` is the whole point of the fix -- verified
    against the extraction chain (`atlas.alpha.investment_case
    .financial_history.extract_market_snapshot`) that it produces a
    document carrying everything "Aktuellt pris" needs, using only
    `GLOBAL_QUOTE`."""

    def test_costs_exactly_one_real_call_never_overview(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _counting_fetcher(
            {"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-21"}}}
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        provider.fetch_price_only(
            company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=7425545000.0
        )
        assert len(fetcher.calls) == 1
        assert "GLOBAL_QUOTE" in fetcher.calls[0]
        assert all("OVERVIEW" not in url for url in fetcher.calls)

    def test_carries_forward_the_given_currency_and_shares_outstanding_unchanged(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-21"}}}
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        doc = provider.fetch_price_only(
            company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=7425545000.0
        )
        assert doc.metadata["share_price"] == 483.24
        assert doc.metadata["currency"] == "USD"
        assert doc.metadata["shares_outstanding"] == 7425545000.0
        assert doc.period_end.isoformat() == "2026-08-21"

    def test_document_shape_matches_what_extract_market_snapshot_needs(self, monkeypatch):
        """The real proof this satisfies Investment Case's "Aktuellt
        pris": run the actual extraction function -- not just inspect
        the document's own fields -- against a document this method
        produced."""
        from atlas.alpha.investment_case.financial_history import extract_market_snapshot

        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-21"}}}
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        doc = provider.fetch_price_only(
            company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=7425545000.0
        )
        business_record = _ingest_for_test(doc)
        snapshot = extract_market_snapshot((business_record,))
        assert snapshot is not None
        assert snapshot.share_price == 483.24
        assert snapshot.currency == "USD"
        assert snapshot.trading_day.isoformat() == "2026-08-21"

    def test_no_currency_confirmed_omits_the_price_rather_than_guessing(self, monkeypatch):
        """Mirrors `fetch`'s own currency-safety rule exactly -- an
        empty/unconfirmed `known_currency` must never let a price
        through under a guessed denomination."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-21"}}}
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        doc = provider.fetch_price_only(
            company_identifier="MSFT", evaluated_at=_NOW, known_currency="", known_shares_outstanding=None
        )
        assert "share_price" not in doc.metadata

    def test_unsupported_currency_raises_rather_than_ingesting(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-21"}}}
        )
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(UnsupportedUnit):
            provider.fetch_price_only(
                company_identifier="MSFT", evaluated_at=_NOW, known_currency="EUR", known_shares_outstanding=None
            )

    def test_missing_price_or_trading_day_raises_malformed_response(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24"}}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch_price_only(
                company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=None
            )

    def test_rate_limited_response_raises_rate_limited(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher({"GLOBAL_QUOTE": {"Information": "Thank you for using Alpha Vantage! ..."}})
        provider = AlphaVantageMarketDataProvider(fetcher)
        with pytest.raises(RateLimited):
            provider.fetch_price_only(
                company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=None
            )

    def test_on_request_hook_fires_exactly_once(self, monkeypatch):
        """The quota-tracking hook -- see `AlphaVantageMarketDataProvider
        .__init__`'s own docstring -- must fire for this real call too,
        exactly as many times as real requests were made (one)."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        fetcher = _fake_fetcher(
            {"GLOBAL_QUOTE": {"Global Quote": {"05. price": "483.24", "07. latest trading day": "2026-08-21"}}}
        )
        calls = []
        provider = AlphaVantageMarketDataProvider(fetcher, on_request=lambda: calls.append(1))
        provider.fetch_price_only(
            company_identifier="MSFT", evaluated_at=_NOW, known_currency="USD", known_shares_outstanding=None
        )
        assert len(calls) == 1


def _ingest_for_test(document: RawBusinessDocument):
    from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

    result = ingest(document, evaluated_at=_NOW)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestPacingSafetyConstant:
    """The pacing calibration sweep (2026-09-04) widened
    `_DEFAULT_INTER_REQUEST_DELAY_SECONDS` from 1.1s to 12.0s. The
    value is an operational safety constant chosen on cost asymmetry --
    a throttled request burns one of only 25 daily calls and returns
    nothing, while waiting longer costs only wall-clock in a background
    job -- and NOT a claim about any documented Alpha Vantage limit.

    These tests pin the properties that make that change meaningful:
    production request starts are genuinely spaced by the wider
    interval, and the pacing math stays exactly as deterministic under
    an injected clock as it was at the narrower value. They deliberately
    do not assert the provider's behaviour under throttling -- that is
    unchanged, and covered elsewhere.
    """

    def test_production_default_is_at_least_the_twelve_second_safety_floor(self):
        """Guards the constant itself. A future edit that narrows the
        spacing back toward the value measured to throttle should fail
        here, loudly, rather than silently start burning quota."""
        assert _DEFAULT_INTER_REQUEST_DELAY_SECONDS >= 12.0

    def test_every_production_request_after_the_first_is_spaced_by_twelve_seconds(self, monkeypatch):
        """The invariant that actually protects quota: with nothing
        injected but a fake sleeper and a clock that never advances on
        its own, a real multi-request production sequence must pace
        every request after the first by the full default interval.

        `fetch()` makes two real requests (GLOBAL_QUOTE, OVERVIEW), and
        `fetch_historical_snapshots()` on the same instance makes one
        more (TIME_SERIES_MONTHLY_ADJUSTED -- its OVERVIEW is reused,
        per ATLAS-033), so three requests means exactly two sleeps."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
                "TIME_SERIES_MONTHLY_ADJUSTED": {
                    "Monthly Adjusted Time Series": {"2023-02-28": {"5. adjusted close": "40.00"}}
                },
            }
        )
        provider = AlphaVantageMarketDataProvider(fetcher, sleeper=sleep_calls.append, clock=_FakeClock())
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        provider.fetch_historical_snapshots(
            company_identifier="AAPL", filing_dates=(date_(2023, 2, 1),), evaluated_at=_NOW
        )
        assert sleep_calls == [12.0, 12.0]
        assert all(seconds >= 12.0 for seconds in sleep_calls)

    def test_pacing_still_sleeps_only_the_remaining_interval_at_the_wider_value(self, monkeypatch):
        """Determinism check at 12.0s: the widened constant must not
        turn the pacing into a flat delay. With 4.5s of real elapsed
        time already spent between two requests, the provider sleeps
        the remaining 7.5s -- exact arithmetic on an injected clock, no
        wall-clock tolerance."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        clock = _FakeClock()
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )

        def advancing_fetcher(url: str, headers: dict | None) -> object:
            clock.advance(4.5)
            return fetcher(url, headers)

        provider = AlphaVantageMarketDataProvider(advancing_fetcher, sleeper=sleep_calls.append, clock=clock)
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == [7.5]

    def test_pacing_does_not_sleep_when_the_full_interval_already_elapsed(self, monkeypatch):
        """The other half of the remaining-interval math at the wider
        value: if more than 12s has genuinely passed, no sleep at all.
        Without this, widening the constant could have made a slow
        real-world caller wait twice."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        clock = _FakeClock()
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )

        def advancing_fetcher(url: str, headers: dict | None) -> object:
            clock.advance(30.0)
            return fetcher(url, headers)

        provider = AlphaVantageMarketDataProvider(advancing_fetcher, sleeper=sleep_calls.append, clock=clock)
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == []

    def test_an_injected_delay_still_overrides_the_default_exactly(self, monkeypatch):
        """Every other pacing test in this file injects its own
        `inter_request_delay_seconds`, which is what keeps them
        deterministic and independent of whatever production ships.
        This pins that override so a future change to the default can
        never silently leak into them."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        sleep_calls: list[float] = []
        fetcher = _fake_fetcher(
            {
                "GLOBAL_QUOTE": {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}},
                "OVERVIEW": {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"},
            }
        )
        provider = AlphaVantageMarketDataProvider(
            fetcher, sleeper=sleep_calls.append, inter_request_delay_seconds=0.25, clock=_FakeClock()
        )
        provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert sleep_calls == [0.25]
        assert _DEFAULT_INTER_REQUEST_DELAY_SECONDS != 0.25

    def test_widening_the_constant_changes_no_request_order_or_document_content(self, monkeypatch):
        """Pacing is a timing concern only. The sequence of outbound
        calls and the documents produced must be byte-for-byte what
        they were before the constant moved."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "k")
        call_order: list[str] = []

        def fetcher(url: str, headers: dict | None) -> object:
            if "GLOBAL_QUOTE" in url:
                call_order.append("GLOBAL_QUOTE")
                return {"Global Quote": {"05. price": "150.00", "07. latest trading day": "2026-08-07"}}
            if "OVERVIEW" in url:
                call_order.append("OVERVIEW")
                return {"Symbol": "AAPL", "Currency": "USD", "SharesOutstanding": "1000000"}
            raise AssertionError(f"unexpected URL: {url}")

        fast = AlphaVantageMarketDataProvider(
            fetcher, sleeper=lambda _: None, inter_request_delay_seconds=1.1, clock=_FakeClock()
        )
        fast_documents = fast.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        fast_order, call_order[:] = list(call_order), []

        slow = AlphaVantageMarketDataProvider(
            fetcher, sleeper=lambda _: None, inter_request_delay_seconds=12.0, clock=_FakeClock()
        )
        slow_documents = slow.fetch(company_identifier="AAPL", evaluated_at=_NOW)

        # Frozen dataclasses, so this compares every field --
        # source_kind, metadata, content_hash and all.
        assert fast_order == call_order == ["GLOBAL_QUOTE", "OVERVIEW"]
        assert list(fast_documents) == list(slow_documents)
        assert [d.source_kind for d in slow_documents] == ["market_data_snapshot"]
