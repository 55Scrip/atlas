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


def _instant_entry(*, end: str, val: float, form: str = "10-K", fp: str = "FY", filed: str, accn: str = "0001234567-24-000001") -> dict:
    """(Company Data Foundation v1) SEC's own real shape for a
    point-in-time (instant-context) fact -- no `start` key at all,
    confirmed live, distinct from `_usd_entry`'s duration shape."""
    return {"end": end, "val": val, "form": form, "fp": fp, "filed": filed, "accn": accn}


def _companyfacts(concepts: dict[str, list[dict]], *, units: dict[str, str] | None = None) -> dict:
    """`units` optionally maps a concept tag to its own XBRL unit key
    (Company Data Foundation v1: `"shares"` for `CommonStockShares
    Outstanding`, `"USD/shares"` for EPS concepts) -- every tag not
    named there defaults to `"USD"`, matching every pre-existing test
    in this file."""
    units = units or {}
    return {
        "cik": 1234567,
        "entityName": "Test Co",
        "facts": {"us-gaap": {tag: {"units": {units.get(tag, "USD"): entries}} for tag, entries in concepts.items()}},
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


class TestAlternativeConceptTags:
    """ATLAS-031A, Issue 3 -- fallback tags added after the post-sprint
    audit found real, live companies (NVDA, MSFT, AMZN) don't use the
    original single mapped tag for these concepts."""

    def test_capex_falls_back_to_productive_assets_tag(self):
        """NVDA's own real tag, confirmed live during the audit --
        PaymentsToAcquirePropertyPlantAndEquipment is absent entirely,
        only the fallback exists."""
        companyfacts = _companyfacts(
            {"PaymentsToAcquireProductiveAssets": [_usd_entry(start="2023-01-01", end="2023-12-31", val=6042, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["capital_expenditure"] == 6042.0

    def test_primary_capex_tag_wins_over_fallback_when_both_present(self):
        companyfacts = _companyfacts(
            {
                "PaymentsToAcquirePropertyPlantAndEquipment": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")],
                "PaymentsToAcquireProductiveAssets": [_usd_entry(start="2023-01-01", end="2023-12-31", val=999, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["capital_expenditure"] == 100.0

    def test_debt_repayment_falls_back_to_repayments_of_debt(self):
        """AMZN/NVDA/AVGO's real tag -- RepaymentsOfLongTermDebt absent."""
        companyfacts = _companyfacts(
            {"RepaymentsOfDebt": [_usd_entry(start="2023-01-01", end="2023-12-31", val=5000, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["debt_repayment"] == 5000.0

    def test_debt_repayment_falls_back_to_repayments_of_commercial_paper(self):
        """MSFT's real tag -- its debt activity is entirely commercial
        paper, confirmed live during the audit."""
        companyfacts = _companyfacts(
            {"RepaymentsOfCommercialPaper": [_usd_entry(start="2023-01-01", end="2023-12-31", val=3000, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["debt_repayment"] == 3000.0

    def test_debt_issuance_falls_back_to_commercial_paper_issuance(self):
        companyfacts = _companyfacts(
            {"ProceedsFromIssuanceOfCommercialPaper": [_usd_entry(start="2023-01-01", end="2023-12-31", val=2000, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["debt_issuance"] == 2000.0

    def test_share_issuance_falls_back_to_stock_options_exercised(self):
        """AMZN/NVDA/META's real tag -- ProceedsFromIssuanceOfCommonStock
        absent, issuance is entirely employee-plan-driven."""
        companyfacts = _companyfacts(
            {
                "StockIssuedDuringPeriodValueStockOptionsExercised": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=800, filed="2024-02-01")
                ]
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["share_issuance"] == 800.0


class TestTickerNormalization:
    """ATLAS-031A, Issue 2 -- provider-local only: SEC's own ticker map
    uses a hyphen where Atlas uses a dot for multi-class tickers. Atlas's
    own ticker identity (RawBusinessDocument.company/identifier) must
    never change as a result."""

    _MULTI_CLASS_TICKER_MAP = {
        "0": {"cik_str": 1067983, "ticker": "BRK-B", "title": "Berkshire Hathaway Inc"},
        "1": {"cik_str": 1067983, "ticker": "BRK-A", "title": "Berkshire Hathaway Inc"},
        "2": {"cik_str": 9999999, "ticker": "XYZ-C", "title": "Fake Multi-Class Co"},
    }

    def test_brk_dot_b_resolves_via_hyphen_normalization(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="BRK.B", evaluated_at=_NOW)
        assert len(docs) == 1

    def test_brk_dot_a_resolves_via_hyphen_normalization(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="BRK.A", evaluated_at=_NOW)
        assert len(docs) == 1

    def test_atlas_ticker_identity_is_unchanged_by_provider_normalization(self):
        """The persisted/returned company identity stays exactly what
        Atlas passed in (BRK.B) -- normalization never leaks past the
        provider's own CIK-lookup boundary."""
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": companyfacts})
        (doc,) = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="BRK.B", evaluated_at=_NOW)
        assert doc.company == "BRK.B"
        assert doc.identifier == "BRK.B:FY:2023-12-31"

    def test_generic_dot_to_hyphen_ticker_not_hardcoded_to_berkshire(self):
        """Proves the normalization is generic, not a Berkshire special
        case -- a fake ticker only present in hyphenated form resolves
        the same way."""
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=50, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="XYZ.C", evaluated_at=_NOW)
        assert len(docs) == 1

    def test_already_correct_format_ticker_still_resolves_directly(self):
        """An already-SEC-format ticker (no dot) must not be broken by
        the new normalization path -- the exact candidate is always
        tried first."""
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="BRK-B", evaluated_at=_NOW)
        assert len(docs) == 1

    def test_ticker_with_no_dot_and_no_match_still_raises_company_not_found(self):
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": {}})
        with pytest.raises(CompanyNotFound):
            SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="NOPE", evaluated_at=_NOW)

    def test_normalization_is_deterministic_across_repeated_calls(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": self._MULTI_CLASS_TICKER_MAP, "companyfacts": companyfacts})
        provider = SecEdgarFundamentalsProvider(fetcher)
        first = provider.fetch(company_identifier="BRK.B", evaluated_at=_NOW)
        second = provider.fetch(company_identifier="BRK.B", evaluated_at=_NOW)
        assert first == second


class TestSignValidation:
    """ATLAS-031A, Issue 4 -- negative CapEx is a real, observed
    data-quality signal, never silently subtracted into FCF."""

    def test_negative_capex_is_dropped_not_used(self):
        companyfacts = _companyfacts(
            {
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")
                ],
                "PaymentsToAcquirePropertyPlantAndEquipment": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=-30, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "capital_expenditure" not in docs[0].metadata
        assert "free_cash_flow" not in docs[0].metadata

    def test_negative_capex_never_silently_inflates_fcf(self):
        """The specific failure mode the audit warned about: OCF - (-30)
        would silently ADD 30 instead of subtracting it. Confirm the
        wrong value (130) is never produced."""
        companyfacts = _companyfacts(
            {
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")
                ],
                "PaymentsToAcquirePropertyPlantAndEquipment": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=-30, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata.get("free_cash_flow") != 130.0

    def test_negative_operating_cash_flow_is_legitimate_and_still_used(self):
        """A cash-burning company genuinely reports negative OCF -- this
        is a real, valid state, never rejected the way negative CapEx
        is. FCF should still be derived (and will itself be negative)."""
        companyfacts = _companyfacts(
            {
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=-50, filed="2024-02-01")
                ],
                "PaymentsToAcquirePropertyPlantAndEquipment": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=20, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["capital_expenditure"] == 20.0
        assert docs[0].metadata["free_cash_flow"] == -70.0

    def test_zero_capex_is_a_legitimate_value_not_dropped(self):
        """Zero is a real, honest fact (no capex spend that period) --
        distinct from a negative value, and must not be treated the
        same way."""
        companyfacts = _companyfacts(
            {
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=100, filed="2024-02-01")
                ],
                "PaymentsToAcquirePropertyPlantAndEquipment": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["capital_expenditure"] == 0.0
        assert docs[0].metadata["free_cash_flow"] == 100.0


class TestIncomeStatementConcepts:
    """Company Data Foundation v1: operating income, net income, EPS."""

    def test_operating_income_persists(self):
        companyfacts = _companyfacts(
            {"OperatingIncomeLoss": [_usd_entry(start="2023-01-01", end="2023-12-31", val=250.0, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["operating_income"] == 250.0

    def test_net_income_persists(self):
        companyfacts = _companyfacts(
            {"NetIncomeLoss": [_usd_entry(start="2023-01-01", end="2023-12-31", val=200.0, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["net_income"] == 200.0

    def test_net_income_falls_back_to_profit_loss(self):
        companyfacts = _companyfacts(
            {"ProfitLoss": [_usd_entry(start="2023-01-01", end="2023-12-31", val=180.0, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["net_income"] == 180.0

    def test_eps_diluted_persists_from_its_own_usd_per_shares_unit(self):
        companyfacts = _companyfacts(
            {"EarningsPerShareDiluted": [_usd_entry(start="2023-01-01", end="2023-12-31", val=2.5, filed="2024-02-01")]},
            units={"EarningsPerShareDiluted": "USD/shares"},
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["eps"] == 2.5

    def test_eps_falls_back_to_basic_when_diluted_is_absent(self):
        companyfacts = _companyfacts(
            {"EarningsPerShareBasic": [_usd_entry(start="2023-01-01", end="2023-12-31", val=2.7, filed="2024-02-01")]},
            units={"EarningsPerShareBasic": "USD/shares"},
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["eps"] == 2.7

    def test_eps_reported_under_the_wrong_unit_is_never_extracted(self):
        """A same-named tag reported under `"USD"` instead of the real
        `"USD/shares"` unit is a malformed/mistagged filing -- honestly
        absent, never silently read from the wrong unit bucket."""
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "EarningsPerShareDiluted": [_usd_entry(start="2023-01-01", end="2023-12-31", val=2.5, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "eps" not in docs[0].metadata


class TestInstantBalanceSheetConcepts:
    """Company Data Foundation v1: cash, debt (current+noncurrent
    policy), shares outstanding -- all point-in-time facts, merged onto
    a fiscal period only by matching `end` date against an already
    -discovered duration period."""

    def test_cash_persists_for_the_matching_fiscal_year_end(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CashAndCashEquivalentsAtCarryingValue": [
                    _instant_entry(end="2023-12-31", val=900.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["cash"] == 900.0

    def test_cash_falls_back_to_the_restricted_cash_combined_concept(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": [
                    _instant_entry(end="2023-12-31", val=950.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["cash"] == 950.0

    def test_total_debt_is_the_sum_of_current_and_noncurrent_when_both_exist(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "LongTermDebtCurrent": [_instant_entry(end="2023-12-31", val=50.0, filed="2024-02-01")],
                "LongTermDebtNoncurrent": [_instant_entry(end="2023-12-31", val=500.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["total_debt"] == 550.0

    def test_total_debt_falls_back_to_the_single_robust_concept_when_the_split_is_unavailable(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "LongTermDebt": [_instant_entry(end="2023-12-31", val=600.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["total_debt"] == 600.0

    def test_total_debt_never_double_counts_when_both_the_split_and_the_single_total_are_reported(self):
        """The current+noncurrent sum and the single-total fallback are
        mutually exclusive branches -- the split, when available, always
        wins; the single total is never added on top of it."""
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "LongTermDebtCurrent": [_instant_entry(end="2023-12-31", val=50.0, filed="2024-02-01")],
                "LongTermDebtNoncurrent": [_instant_entry(end="2023-12-31", val=500.0, filed="2024-02-01")],
                "LongTermDebt": [_instant_entry(end="2023-12-31", val=999.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["total_debt"] == 550.0

    def test_total_debt_current_falls_back_to_short_term_borrowings(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "ShortTermBorrowings": [_instant_entry(end="2023-12-31", val=40.0, filed="2024-02-01")],
                "LongTermDebtNoncurrent": [_instant_entry(end="2023-12-31", val=500.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["total_debt"] == 540.0

    def test_total_debt_absent_when_neither_split_nor_single_total_exists(self):
        """Never fabricated from one side alone -- missing current with
        no noncurrent and no single-total concept means total debt is
        honestly undetermined for this period."""
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "LongTermDebtCurrent": [_instant_entry(end="2023-12-31", val=50.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "total_debt" not in docs[0].metadata

    def test_shares_outstanding_persists_from_its_own_shares_unit(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CommonStockSharesOutstanding": [_instant_entry(end="2023-12-31", val=1_000_000.0, filed="2024-02-01")],
            },
            units={"CommonStockSharesOutstanding": "shares"},
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["shares_outstanding"] == 1_000_000.0

    def test_shares_outstanding_reported_under_the_wrong_unit_is_never_extracted(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CommonStockSharesOutstanding": [_instant_entry(end="2023-12-31", val=1_000_000.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "shares_outstanding" not in docs[0].metadata

    def test_instant_facts_never_fabricate_a_period_with_no_duration_data(self):
        """An instant fact whose `end` date matches no fiscal period
        discovered from duration concepts is simply dropped -- it never
        invents a period whose own `start` date is unknown."""
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CashAndCashEquivalentsAtCarryingValue": [
                    _instant_entry(end="2023-12-31", val=900.0, filed="2024-02-01"),
                    _instant_entry(end="2022-12-31", val=800.0, filed="2023-02-01"),  # no matching duration period
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert len(docs) == 1  # not two -- the 2022 instant value never became its own document
        assert docs[0].metadata["cash"] == 900.0

    def test_instant_amendment_keeps_the_most_recently_filed_value(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CashAndCashEquivalentsAtCarryingValue": [
                    _instant_entry(end="2023-12-31", val=900.0, filed="2024-02-01"),
                    _instant_entry(end="2023-12-31", val=920.0, filed="2024-05-01"),
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["cash"] == 920.0

    def test_quarterly_instant_entries_are_excluded(self):
        """Instant facts still require `form == "10-K"` -- a quarterly
        (10-Q) balance-sheet value is never picked up."""
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "CashAndCashEquivalentsAtCarryingValue": [
                    _instant_entry(end="2023-12-31", val=900.0, form="10-Q", filed="2023-11-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "cash" not in docs[0].metadata


class TestFinancialStatementIntelligenceConcepts:
    """Capability Expansion Sprint 3 -- the new Income Statement/Balance
    Sheet concepts and their derived figures (`ebitda`/`working_capital`
    /`tangible_assets`)."""

    def test_gross_profit_persists(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "GrossProfit": [_usd_entry(start="2023-01-01", end="2023-12-31", val=400.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["gross_profit"] == 400.0

    def test_gross_profit_absent_when_not_reported(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "gross_profit" not in docs[0].metadata

    def test_operating_cash_flow_now_persists_directly(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "NetCashProvidedByUsedInOperatingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=250.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["operating_cash_flow"] == 250.0

    def test_investing_and_financing_cash_flow_persist(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "NetCashProvidedByUsedInInvestingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=-80.0, filed="2024-02-01")
                ],
                "NetCashProvidedByUsedInFinancingActivities": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=-60.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["investing_cash_flow"] == -80.0
        assert docs[0].metadata["financing_cash_flow"] == -60.0

    def test_ebitda_is_derived_from_operating_income_and_depreciation_amortization(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "OperatingIncomeLoss": [_usd_entry(start="2023-01-01", end="2023-12-31", val=200.0, filed="2024-02-01")],
                "DepreciationDepletionAndAmortization": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=50.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["ebitda"] == 250.0
        assert "_depreciation_and_amortization" not in docs[0].metadata

    def test_ebitda_absent_when_depreciation_and_amortization_is_not_reported(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "OperatingIncomeLoss": [_usd_entry(start="2023-01-01", end="2023-12-31", val=200.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "ebitda" not in docs[0].metadata

    def test_equity_current_assets_and_current_liabilities_persist(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "StockholdersEquity": [_instant_entry(end="2023-12-31", val=700.0, filed="2024-02-01")],
                "AssetsCurrent": [_instant_entry(end="2023-12-31", val=300.0, filed="2024-02-01")],
                "LiabilitiesCurrent": [_instant_entry(end="2023-12-31", val=120.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["equity"] == 700.0
        assert docs[0].metadata["current_assets"] == 300.0
        assert docs[0].metadata["current_liabilities"] == 120.0
        assert docs[0].metadata["working_capital"] == 180.0

    def test_working_capital_absent_when_only_one_side_is_reported(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "AssetsCurrent": [_instant_entry(end="2023-12-31", val=300.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "working_capital" not in docs[0].metadata

    def test_tangible_assets_subtracts_goodwill_and_intangibles_from_total_assets(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "Assets": [_instant_entry(end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "Goodwill": [_instant_entry(end="2023-12-31", val=200.0, filed="2024-02-01")],
                "IntangibleAssetsNetExcludingGoodwill": [_instant_entry(end="2023-12-31", val=50.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["total_assets"] == 1000.0
        assert docs[0].metadata["goodwill"] == 200.0
        assert docs[0].metadata["intangible_assets"] == 50.0
        assert docs[0].metadata["tangible_assets"] == 750.0

    def test_tangible_assets_equals_total_assets_when_no_goodwill_or_intangibles_reported(self):
        """A company genuinely reporting no goodwill/intangibles is a
        real zero for those two, not a missing value -- their absence
        must not block the subtraction."""
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "Assets": [_instant_entry(end="2023-12-31", val=1000.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["tangible_assets"] == 1000.0

    def test_tangible_assets_absent_when_total_assets_is_not_reported(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "Goodwill": [_instant_entry(end="2023-12-31", val=200.0, filed="2024-02-01")],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "tangible_assets" not in docs[0].metadata


class TestCapitalAllocationIntelligenceConcepts:
    """Capability Expansion Sprint 4 -- the one genuinely missing
    concept per this sprint's own Phase 2 audit (acquisitions/disposals/
    treasury share count; every other Capital Allocation fact already
    existed before this sprint)."""

    def test_acquisitions_persist(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "PaymentsToAcquireBusinessesNetOfCashAcquired": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=500.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["acquisitions"] == 500.0

    def test_disposals_persist(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "ProceedsFromDivestitureOfBusinesses": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=80.0, filed="2024-02-01")
                ],
            }
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["disposals"] == 80.0

    def test_acquisitions_and_disposals_absent_when_not_reported(self):
        companyfacts = _companyfacts(
            {"Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")]}
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "acquisitions" not in docs[0].metadata
        assert "disposals" not in docs[0].metadata

    def test_treasury_shares_acquired_persists_under_its_own_shares_unit(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "TreasuryStockSharesAcquired": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=1_000_000.0, filed="2024-02-01")
                ],
            },
            units={"TreasuryStockSharesAcquired": "shares"},
        )
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert docs[0].metadata["treasury_shares_acquired"] == 1_000_000.0

    def test_treasury_shares_acquired_reported_under_the_wrong_unit_is_never_extracted(self):
        companyfacts = _companyfacts(
            {
                "Revenues": [_usd_entry(start="2023-01-01", end="2023-12-31", val=1000.0, filed="2024-02-01")],
                "TreasuryStockSharesAcquired": [
                    _usd_entry(start="2023-01-01", end="2023-12-31", val=1_000_000.0, filed="2024-02-01")
                ],
            },
        )  # deliberately no `units=` override -- defaults to "USD", the wrong unit for a share count
        fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
        docs = SecEdgarFundamentalsProvider(fetcher).fetch(company_identifier="AAPL", evaluated_at=_NOW)
        assert "treasury_shares_acquired" not in docs[0].metadata
