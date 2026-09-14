"""Historical Market-Data Provenance: what the adapters keep from each
provider response, and what the market-data reader makes of it.

Fixture bars are copied from the one approved live
`TIME_SERIES_MONTHLY_ADJUSTED` response for AAPL (2026-09-13): the fields
`1. open` ... `7. dividend amount`, no split coefficient. All fake
fetchers -- no network anywhere in this file.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date as date_
from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.business_data.pipeline import DuplicateRecord, IngestedRecord, ingest
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.analysis_engine.valuation.facts import (
    PriceBasis,
    ValuationFactKind,
    extract_valuation_facts,
    market_price_provenance,
)
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider
from tests.unit.business_data_providers.test_sec_edgar import (
    _TICKER_MAP,
    _companyfacts,
    _instant_entry,
    _usd_entry,
)
from tests.unit.business_data_providers.test_sec_edgar import _fake_fetcher as _sec_fetcher

_FETCHED = datetime(2026, 8, 10, tzinfo=timezone.utc)
_REFETCHED = datetime(2026, 8, 18, tzinfo=timezone.utc)

#: Real bars: a pre-split month (raw 595.32 against adjusted 17.8810), a
#: dividend month on the raw basis ($3.29 before the 2014 split), and the
#: month with the $0.27 dividend that rescaled every earlier adjusted close.
_BAR_2012_10 = {
    "1. open": "671.5000", "2. high": "676.7500", "3. low": "587.7000", "4. close": "595.3200",
    "5. adjusted close": "17.8810", "6. volume": "433672500", "7. dividend amount": "0.0000",
}
_BAR_2014_05 = {
    "1. open": "592.0000", "2. high": "644.1700", "3. low": "580.3300", "4. close": "633.0000",
    "5. adjusted close": "19.8081", "6. volume": "204845300", "7. dividend amount": "3.2900",
}


def _av_fetcher(series: dict, *, currency: str = "USD", quote_price: str = "332.27"):
    responses = {
        "TIME_SERIES_MONTHLY_ADJUSTED": {"Monthly Adjusted Time Series": series},
        "OVERVIEW": {"Symbol": "AAPL", "Currency": currency, "SharesOutstanding": "14594180000"},
        "GLOBAL_QUOTE": {"Global Quote": {"05. price": quote_price, "07. latest trading day": "2026-09-11"}},
    }

    def fetcher(url, headers):
        for key, value in responses.items():
            if f"function={key}" in url:
                return value
        raise AssertionError(f"unexpected URL: {url}")

    return fetcher


def _historical(series: dict, filing: date_, **kwargs):
    provider = AlphaVantageMarketDataProvider(_av_fetcher(series, **kwargs), sleeper=lambda s: None, api_key="k")
    (doc,) = provider.fetch_historical_snapshots(company_identifier="AAPL", filing_dates=(filing,), evaluated_at=_FETCHED)
    return doc


def _record(doc, *, evaluated_at=_FETCHED, existing=()):
    result = ingest(doc, evaluated_at=evaluated_at, existing_records=existing)
    assert isinstance(result, IngestedRecord), result
    return result.record


class TestHistoricalBarProvenance:
    def test_raw_close_is_kept_exactly_as_the_provider_reported_it(self):
        doc = _historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30))
        assert doc.metadata["raw_close"] == 595.32

    def test_share_price_stays_the_adjusted_close_and_says_so(self):
        doc = _historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30))
        assert doc.metadata["share_price"] == 17.881
        assert doc.metadata["price_basis"] == "split_and_dividend_adjusted"

    def test_the_dividend_is_kept_per_share_as_reported(self):
        doc = _historical({"2014-05-30": _BAR_2014_05}, date_(2014, 5, 1))
        assert doc.metadata["dividend_amount"] == 3.29

    def test_an_explicit_zero_dividend_stays_zero(self):
        doc = _historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30))
        assert doc.metadata["dividend_amount"] == 0.0

    def test_a_missing_dividend_stays_missing_never_zero(self):
        bar = {k: v for k, v in _BAR_2012_10.items() if k != "7. dividend amount"}
        doc = _historical({"2012-10-31": bar}, date_(2012, 10, 30))
        assert "dividend_amount" not in doc.metadata

    def test_no_raw_close_is_derived_when_the_provider_sent_none(self):
        bar = {k: v for k, v in _BAR_2012_10.items() if k != "4. close"}
        doc = _historical({"2012-10-31": bar}, date_(2012, 10, 30))
        assert "raw_close" not in doc.metadata
        assert doc.metadata["share_price"] == 17.881

    def test_an_unconfirmed_currency_carries_no_price_of_any_kind(self):
        doc = _historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30), currency="")
        assert not {"share_price", "raw_close", "dividend_amount", "price_basis"} & set(doc.metadata)


class TestCurrentQuoteProvenance:
    def test_a_current_quote_is_a_raw_price(self):
        provider = AlphaVantageMarketDataProvider(_av_fetcher({}), sleeper=lambda s: None, api_key="k")
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_FETCHED)
        assert doc.metadata["price_basis"] == "raw"
        assert "raw_close" not in doc.metadata  # share_price is itself the raw price

    def test_a_price_only_refresh_is_a_raw_price(self):
        provider = AlphaVantageMarketDataProvider(_av_fetcher({}), sleeper=lambda s: None, api_key="k")
        doc = provider.fetch_price_only(
            company_identifier="AAPL", evaluated_at=_FETCHED, known_currency="USD", known_shares_outstanding=1.0
        )
        assert doc.metadata["price_basis"] == "raw"


class TestReadingProvenanceBack:
    def test_a_new_historical_record_reads_as_adjusted_with_its_raw_close(self):
        record = _record(_historical({"2014-05-30": _BAR_2014_05}, date_(2014, 5, 1)))
        p = market_price_provenance(record)
        assert (p.basis, p.basis_recorded, p.share_price, p.raw_close, p.dividend_amount) == (
            PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED, True, 19.8081, 633.0, 3.29,
        )
        assert p.observed_on == "2014-05-30"
        assert p.retrieved_at == _FETCHED

    def test_a_legacy_historical_row_still_means_adjusted_never_raw(self):
        """A snapshot written before the basis was stored: its endpoint
        fixes the basis; nothing raw is reconstructed."""
        legacy = _historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30))
        legacy = _legacy(legacy)
        p = market_price_provenance(_record(legacy))
        assert (p.basis, p.basis_recorded, p.raw_close, p.dividend_amount) == (
            PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED, False, None, None,
        )
        assert p.share_price == 17.881

    def test_a_legacy_current_quote_reads_as_raw(self):
        provider = AlphaVantageMarketDataProvider(_av_fetcher({}), sleeper=lambda s: None, api_key="k")
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_FETCHED)
        p = market_price_provenance(_record(_legacy(doc)))
        assert (p.basis, p.basis_recorded) == (PriceBasis.RAW, False)

    def test_a_snapshot_with_no_basis_and_no_known_endpoint_is_unknown(self):
        doc = _legacy(_historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30)))
        doc = type(doc)(**{**doc.__dict__, "raw_reference": "https://example.invalid/prices"})
        assert market_price_provenance(_record(doc)).basis is PriceBasis.UNKNOWN


class TestValuationKeepsReadingTheAdjustedPrice:
    def test_the_share_price_fact_is_the_adjusted_close_not_the_raw_close(self):
        record = _record(_historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30)))
        facts = extract_valuation_facts(record, evaluated_at=_FETCHED)
        assert {f.kind: f.value for f in facts} == {
            ValuationFactKind.SHARE_PRICE: 17.881,
            ValuationFactKind.SHARES_OUTSTANDING: 14594180000.0,
        }

    def test_provenance_adds_no_valuation_fact_to_a_legacy_equivalent_snapshot(self):
        new = _record(_historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30)))
        old = _record(_legacy(_historical({"2012-10-31": _BAR_2012_10}, date_(2012, 10, 30))))
        strip = lambda facts: sorted((f.kind, f.value, f.unit, f.period) for f in facts)
        assert strip(extract_valuation_facts(new, evaluated_at=_FETCHED)) == strip(
            extract_valuation_facts(old, evaluated_at=_FETCHED)
        )

    def test_no_methodology_identity_moves_for_provenance(self):
        from atlas.analysis_engine.methodology import ANALYSIS_METHODOLOGY
        from atlas.analysis_engine.valuation.cash_flow import FCF_YIELD_METHODOLOGY

        assert FCF_YIELD_METHODOLOGY == "fiscal_epoch_v2"
        assert ANALYSIS_METHODOLOGY == (
            "financial_risk=debt_burden_v2;outlook=sensitivity_v2;"
            "rolling_growth=fiscal_year_windows_v2;valuation=fiscal_epoch_v2"
        )


class TestAdjustedRevisionOnReFetch:
    """The AAPL control: a dividend after the first fetch rescaled every
    earlier adjusted close by 0.999125; the raw close cannot move."""

    _V1 = {**_BAR_2012_10, "5. adjusted close": "17.8967"}
    _V2 = _BAR_2012_10

    def test_a_revised_adjusted_close_is_a_new_version_beside_the_same_raw_close(self):
        first = _record(_historical({"2012-10-31": self._V1}, date_(2012, 10, 30)))
        second_doc = AlphaVantageMarketDataProvider(
            _av_fetcher({"2012-10-31": self._V2}), sleeper=lambda s: None, api_key="k"
        ).fetch_historical_snapshots(company_identifier="AAPL", filing_dates=(date_(2012, 10, 30),), evaluated_at=_REFETCHED)[0]
        second = _record(second_doc, evaluated_at=_REFETCHED, existing=(first,))
        assert second.version.version_number == 2 and second.version.supersedes == first.id
        (latest,) = latest_versions((first, second))
        a, b = market_price_provenance(first), market_price_provenance(latest)
        assert a.raw_close == b.raw_close == 595.32
        assert (a.share_price, b.share_price) == (17.8967, 17.881)
        assert round(b.share_price / a.share_price, 6) == 0.999123
        assert (a.retrieved_at, b.retrieved_at) == (_FETCHED, _REFETCHED)

    def test_an_identical_re_fetch_writes_nothing_new(self):
        first = _record(_historical({"2012-10-31": self._V2}, date_(2012, 10, 30)))
        again = AlphaVantageMarketDataProvider(
            _av_fetcher({"2012-10-31": self._V2}), sleeper=lambda s: None, api_key="k"
        ).fetch_historical_snapshots(company_identifier="AAPL", filing_dates=(date_(2012, 10, 30),), evaluated_at=_REFETCHED)[0]
        assert isinstance(ingest(again, evaluated_at=_REFETCHED, existing_records=(first,)), DuplicateRecord)


class TestShareCountFilingProvenance:
    """The period-end count keeps the filing it came from and what the
    first filing said -- here a later comparative restated for a 7-for-1
    split."""

    def _docs(self, *, restated_filed: str = "2014-10-27"):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2012-09-30", end="2013-09-28", val=1000.0, filed="2013-10-30")],
                "CommonStockSharesOutstanding": [
                    _instant_entry(end="2013-09-28", val=899_213_000.0, filed="2013-10-30", accn="0001193125-13-416534"),
                    _instant_entry(end="2013-09-28", val=6_294_494_000.0, filed=restated_filed, accn="0001193125-14-383437"),
                ],
            },
            units={"CommonStockSharesOutstanding": "shares"},
        )
        fetcher = _sec_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        return SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_FETCHED)

    def test_the_stored_count_names_its_filing_and_the_first_report(self):
        (doc,) = self._docs()
        m = doc.metadata
        assert m["shares_outstanding"] == 6_294_494_000.0  # unchanged: the latest filing's value
        assert (m["shares_outstanding_filed"], m["shares_outstanding_accession"]) == ("2014-10-27", "0001193125-14-383437")
        assert (
            m["shares_outstanding_first_reported"],
            m["shares_outstanding_first_reported_filed"],
            m["shares_outstanding_first_reported_accession"],
        ) == (899_213_000.0, "2013-10-30", "0001193125-13-416534")

    def test_every_count_provenance_key_is_one_an_enrichment_may_add(self):
        from atlas.analysis_engine.business_data.pipeline import SHARE_COUNT_PROVENANCE_KEYS

        (doc,) = self._docs()
        written = {k for k in doc.metadata if k.startswith("shares_outstanding_")}
        assert written == SHARE_COUNT_PROVENANCE_KEYS

    def test_filing_provenance_never_changes_the_statement_content_hash(self):
        (a,) = self._docs(restated_filed="2014-10-27")
        (b,) = self._docs(restated_filed="2014-11-03")
        assert a.content_hash == b.content_hash
        assert a.metadata["shares_outstanding_filed"] != b.metadata["shares_outstanding_filed"]

    def test_the_first_report_does_not_depend_on_entry_order(self):
        (a,) = self._docs()
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2012-09-30", end="2013-09-28", val=1000.0, filed="2013-10-30")],
                "CommonStockSharesOutstanding": [
                    _instant_entry(end="2013-09-28", val=6_294_494_000.0, filed="2014-10-27", accn="0001193125-14-383437"),
                    _instant_entry(end="2013-09-28", val=899_213_000.0, filed="2013-10-30", accn="0001193125-13-416534"),
                ],
            },
            units={"CommonStockSharesOutstanding": "shares"},
        )
        fetcher = _sec_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        (b,) = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_FETCHED)
        assert a.metadata == b.metadata and a.content_hash == b.content_hash

    def test_a_statement_without_a_count_carries_no_count_provenance(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2012-09-30", end="2013-09-28", val=1000.0, filed="2013-10-30")]}
        )
        fetcher = _sec_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        (doc,) = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_FETCHED)
        assert not [k for k in doc.metadata if k.startswith("shares_outstanding")]


def _legacy(doc):
    """`doc` as the adapter wrote it before this sprint: no basis, no raw
    close, no dividend -- and the content hash it had then."""
    metadata = {k: v for k, v in doc.metadata.items() if k not in ("price_basis", "raw_close", "dividend_amount")}
    content_hash = hashlib.sha256(
        json.dumps({"date": doc.period_start.isoformat(), **metadata}, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return type(doc)(**{**doc.__dict__, "metadata": metadata, "content_hash": content_hash})
