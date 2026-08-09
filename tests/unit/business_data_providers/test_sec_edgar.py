"""SEC EDGAR fundamentals provider contract tests (ATLAS-031, Phase 33).

All fake -- no live network anywhere in this file. Uses the same
injectable-`fetch_json`-callable pattern `atlas.providers.yahoo`
already established (`fetcher: JsonFetcher | None`), confirmed in the
Phase 1 audit as the way to test a network-calling provider without an
HTTP-mocking library (none is installed in this repository).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.business_data_providers.errors import (
    CompanyNotFound,
    MalformedProviderResponse,
    MissingRequiredField,
)
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)

_TICKER_MAP = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1234567, "ticker": "TESTCO", "title": "Test Co"},
}


def _usd_entry(*, start: str, end: str, val: float, form: str = "10-K", fp: str = "FY", filed: str, accn: str = "0001234567-24-000001") -> dict:
    return {"start": start, "end": end, "val": val, "form": form, "fp": fp, "filed": filed, "accn": accn}


def _companyfacts(concepts: dict[str, list[dict]]) -> dict:
    return {"cik": 1234567, "entityName": "Test Co", "facts": {"us-gaap": {tag: {"units": {"USD": entries}} for tag, entries in concepts.items()}}}


def _fake_fetcher(responses: dict[str, object]):
    def fetcher(url: str, headers: dict | None) -> object:
        for key, value in responses.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value
        raise AssertionError(f"unexpected URL in test: {url}")

    return fetcher


class TestCompanyResolution:
    def test_unknown_ticker_raises_company_not_found(self):
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP})
        provider = SecEdgarFundamentalsProvider(fetcher)
        with pytest.raises(CompanyNotFound):
            provider.fetch(company_identifier="NOPE", evaluated_at=_NOW)

    def test_ticker_map_not_a_dict_raises_malformed(self):
        fetcher = _fake_fetcher({"company_tickers.json": ["not", "a", "dict"]})
        provider = SecEdgarFundamentalsProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_ticker_resolution_is_case_insensitive(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [
                    _usd_entry(start="2022-01-01", end="2022-12-31", val=100, filed="2023-02-01"),
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=110, filed="2024-02-01"),
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="aapl", evaluated_at=_NOW)
        assert len(docs) == 2
        assert all(d.company == "AAPL" for d in docs)


class TestCompanyfactsShape:
    def test_no_facts_key_raises_malformed(self):
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": {"cik": 1}})
        provider = SecEdgarFundamentalsProvider(fetcher)
        with pytest.raises(MalformedProviderResponse):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_empty_us_gaap_raises_missing_required_field(self):
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": {"facts": {"us-gaap": {}}}})
        provider = SecEdgarFundamentalsProvider(fetcher)
        with pytest.raises(MissingRequiredField):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)

    def test_no_annual_periods_found_raises_missing_required_field(self):
        """Only quarterly (fp != 'FY') facts exist -- honestly reported
        as no usable data, never silently treated as annual."""
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-03-31", val=25, fp="Q1", filed="2023-04-15")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        with pytest.raises(MissingRequiredField):
            provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)


class TestPeriodExtraction:
    def test_three_annual_periods_produce_three_documents_in_chronological_order(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [
                    _usd_entry(start="2021-01-01", end="2021-12-31", val=100, filed="2022-02-01"),
                    _usd_entry(start="2022-01-01", end="2022-12-31", val=110, filed="2023-02-01"),
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=120, filed="2024-02-01"),
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert [d.period_end.isoformat() for d in docs] == ["2021-12-31", "2022-12-31", "2023-12-31"]
        assert [d.metadata["revenue"] for d in docs] == [100.0, 110.0, 120.0]

    def test_provider_newest_first_ordering_does_not_affect_result(self):
        """SEC's own JSON array order is irrelevant -- output is always
        sorted by (start, end), never by array position."""
        companyfacts = _companyfacts(
            {
                "Revenues": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=120, filed="2024-02-01"),
                    _usd_entry(start="2021-01-01", end="2021-12-31", val=100, filed="2022-02-01"),
                    _usd_entry(start="2022-01-01", end="2022-12-31", val=110, filed="2023-02-01"),
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert [d.period_end.isoformat() for d in docs] == ["2021-12-31", "2022-12-31", "2023-12-31"]

    def test_quarterly_entries_are_excluded_from_annual_documents(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=120, filed="2024-02-01"),
                    _usd_entry(start="2023-01-01", end="2023-03-31", val=25, fp="Q1", filed="2023-04-15"),
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["revenue"] == 120.0

    def test_duplicate_provider_period_keeps_the_most_recently_filed_entry(self):
        """Two entries for the identical (start, end) -- an amendment
        already reflected in SEC's own data. The later `filed` date
        wins, never the array order."""
        companyfacts = _companyfacts(
            {
                "Revenues": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01", accn="orig"),
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=105, filed="2024-05-01", accn="amended"),
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["revenue"] == 105.0
        assert docs[0].metadata["sec_accession"] == "amended"

    def test_missing_intermediate_period_is_simply_absent_not_fabricated(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [
                    _usd_entry(start="2021-01-01", end="2021-12-31", val=100, filed="2022-02-01"),
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=120, filed="2024-02-01"),
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert [d.period_end.isoformat() for d in docs] == ["2021-12-31", "2023-12-31"]

    def test_restated_period_republished_with_a_changed_value_across_two_fetches(self):
        """Simulates a real restatement: the exact same provider period
        reported with a different value on a later fetch. The provider
        itself always reflects the latest data given to it; whether
        that becomes a new BusinessRecord version is `ingest`'s job,
        tested in test_service.py."""
        original = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")]}
        )
        restated = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=95, filed="2024-08-01", accn="restated")]}
        )
        fetcher_v1 = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": original})
        docs_v1 = SecEdgarFundamentalsProvider(fetcher_v1).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        fetcher_v2 = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": restated})
        docs_v2 = SecEdgarFundamentalsProvider(fetcher_v2).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs_v1[0].metadata["revenue"] == 100.0
        assert docs_v2[0].metadata["revenue"] == 95.0
        assert docs_v1[0].content_hash != docs_v2[0].content_hash


class TestFreeCashFlowDerivation:
    def test_fcf_computed_as_operating_cash_flow_minus_capex(self):
        companyfacts = _companyfacts(
            {
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")
                ],
                "PaymentsToAcquirePropertyPlantAndEquipment": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=30, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["free_cash_flow"] == 70.0
        assert "_operating_cash_flow" not in docs[0].metadata

    def test_fcf_absent_when_only_one_side_is_present(self):
        """Never invented from one side alone (Phase 6's own "no silent
        unit conversion / no invented fact" rule)."""
        companyfacts = _companyfacts(
            {
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "free_cash_flow" not in docs[0].metadata


class TestPartialCoverage:
    def test_capital_allocation_partial_signal_coverage_is_honest(self):
        """Only buybacks reported -- issuance, debt sides, dividends,
        capex are simply absent from metadata, never defaulted to 0."""
        companyfacts = _companyfacts(
            {"PaymentsForRepurchaseOfCommonStock": [_usd_entry(start="2023-01-01", end="2023-12-31", val=50, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        docs = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["share_buybacks"] == 50.0
        for absent_key in ("share_issuance", "debt_issuance", "debt_repayment", "dividends", "capital_expenditure"):
            assert absent_key not in docs[0].metadata


class TestDocumentShape:
    def test_documents_are_tagged_financial_statement_and_carry_provenance_metadata(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=120, filed="2024-02-01", accn="0001234567-24-000099")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        (doc,) = provider.fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert isinstance(doc, RawBusinessDocument)
        assert doc.source_kind == "financial_statement"
        assert doc.provider_id == "sec_edgar"
        assert doc.metadata["currency"] == "USD"
        assert doc.metadata["sec_accession"] == "0001234567-24-000099"
        assert doc.identifier == "AAPL:FY:2023-12-31"
