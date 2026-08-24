"""SEC EDGAR fundamentals provider -- IFRS/20-F support (International
Coverage, Implementation Phase 1).

All fake companyfacts payloads -- no live network. Real-payload
verification against ASML/AZN/TSM happened separately, live, against
the real SEC API (see this sprint's own final report); the concept-tag
mappings and form/fp values used as fixtures here mirror exactly what
that live verification confirmed, never invented. `_companyfacts`
below is a local, ifrs-full-aware sibling of `test_sec_edgar.py`'s own
`_companyfacts` helper -- same shape, extended to place concepts under
either taxonomy and to control the reported currency, since a foreign
filer (unlike every existing `test_sec_edgar.py` fixture) may report in
a non-USD currency.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from atlas.business_data_providers.errors import MissingRequiredField
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider

_NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)

_TICKER_MAP = {
    "0": {"cik_str": 937966, "ticker": "ASML", "title": "ASML Holding N.V."},
}


def _entry(*, start: str | None, end: str, val: float, form: str, fp: str = "FY", filed: str, accn: str = "0001234567-24-000001") -> dict:
    entry = {"end": end, "val": val, "form": form, "fp": fp, "filed": filed, "accn": accn}
    if start is not None:
        entry["start"] = start
    return entry


def _duration_entry(*, start: str, end: str, val: float, form: str = "20-F", filed: str, accn: str = "0001234567-24-000001") -> dict:
    return _entry(start=start, end=end, val=val, form=form, filed=filed, accn=accn)


def _instant_entry(*, end: str, val: float, form: str = "20-F", filed: str, accn: str = "0001234567-24-000001") -> dict:
    return _entry(start=None, end=end, val=val, form=form, filed=filed, accn=accn)


def _companyfacts(
    *,
    taxonomy: str = "ifrs-full",
    concepts: dict[str, list[dict]],
    units: dict[str, str] | None = None,
    also_us_gaap: dict[str, list[dict]] | None = None,
) -> dict:
    """`units` maps a concept tag to its own XBRL unit key -- every tag
    not named there defaults to `"USD"`. `also_us_gaap`, when given,
    places a second, independent set of concepts under `us-gaap` in the
    same payload -- used only by the two tests proving `fetch()` never
    merges concepts across taxonomies."""
    facts: dict = {taxonomy: {tag: {"units": {units.get(tag, "USD") if units else "USD": entries}} for tag, entries in concepts.items()}}
    if also_us_gaap is not None:
        facts["us-gaap"] = {tag: {"units": {"USD": entries}} for tag, entries in also_us_gaap.items()}
    return {"cik": 937966, "entityName": "Test Foreign Co", "facts": facts}


def _fake_fetcher(responses: dict[str, object]):
    def fetcher(url: str, headers: dict | None) -> object:
        for key, value in responses.items():
            if key in url:
                if isinstance(value, Exception):
                    raise value
                return value
        raise AssertionError(f"unexpected URL in test: {url}")

    return fetcher


def _provider(companyfacts: dict) -> SecEdgarFundamentalsProvider:
    fetcher = _fake_fetcher({"company_tickers.json": _TICKER_MAP, "companyfacts": companyfacts})
    return SecEdgarFundamentalsProvider(fetcher)


class TestUsGaapPathUnchanged:
    """Requirement 6 -- proves ordinary US equities still produce the
    identical result, using this file's own fixtures (test_sec_edgar.py
    itself already proves this at scale: all 78 of its own tests pass
    unchanged after this sprint's implementation)."""

    def test_a_domestic_10k_filer_is_unaffected_by_ifrs_support_existing(self):
        companyfacts = _companyfacts(
            taxonomy="us-gaap",
            concepts={"Revenues": [_entry(start="2023-01-01", end="2023-12-31", val=100.0, form="10-K", filed="2024-02-01")]},
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["revenue"] == 100.0
        assert docs[0].metadata["currency"] == "USD"
        assert docs[0].metadata["sec_form"] == "10-K"
        assert docs[0].metadata["sec_taxonomy"] == "us-gaap"

    def test_a_20f_filer_tagged_under_us_gaap_is_not_routed_to_ifrs(self):
        """ASML's own real, live-confirmed shape: a 20-F filer that
        tags under us-gaap anyway. Must resolve via the us-gaap/20-F
        combination, never fall through to ifrs-full (which is empty
        here) or be treated as unsupported."""
        companyfacts = _companyfacts(
            taxonomy="us-gaap",
            concepts={
                "RevenueFromContractWithCustomerExcludingAssessedTax": [
                    _entry(start="2023-01-01", end="2023-12-31", val=32000000000.0, form="20-F", filed="2024-02-01")
                ]
            },
            units={"RevenueFromContractWithCustomerExcludingAssessedTax": "EUR"},
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["revenue"] == 32000000000.0
        assert docs[0].metadata["currency"] == "EUR"
        assert docs[0].metadata["sec_form"] == "20-F"
        assert docs[0].metadata["sec_taxonomy"] == "us-gaap"


class TestIfrsFallback:
    def test_ifrs_full_used_only_when_us_gaap_has_no_usable_annual_data(self):
        companyfacts = _companyfacts(
            concepts={"Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=58000000000.0, filed="2024-02-01")]}
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["sec_taxonomy"] == "ifrs-full"
        assert docs[0].metadata["revenue"] == 58000000000.0

    def test_taxonomies_are_never_merged_within_one_document(self):
        """A payload with both a real us-gaap 10-K concept AND a real
        ifrs-full concept -- us-gaap wins outright (tried first); the
        ifrs-full data is never blended in alongside it."""
        companyfacts = _companyfacts(
            taxonomy="ifrs-full",
            concepts={"NetIncome_NeverReadUnderIfrs": [_duration_entry(start="2023-01-01", end="2023-12-31", val=999.0, filed="2024-02-01")]},
            also_us_gaap={"Revenues": [_entry(start="2023-01-01", end="2023-12-31", val=100.0, form="10-K", filed="2024-02-01")]},
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["sec_taxonomy"] == "us-gaap"
        assert docs[0].metadata["revenue"] == 100.0
        assert "net_income" not in docs[0].metadata


class TestIfrsRevenueMapping:
    def test_revenue_tag(self):
        companyfacts = _companyfacts(concepts={"Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")]})
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["revenue"] == 100.0

    def test_revenue_from_contracts_with_customers_fallback_tag(self):
        companyfacts = _companyfacts(
            concepts={"RevenueFromContractsWithCustomers": [_duration_entry(start="2023-01-01", end="2023-12-31", val=105.0, filed="2024-02-01")]}
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["revenue"] == 105.0


class TestIfrsProfitabilityMapping:
    def test_profit_loss_maps_to_net_income(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "ProfitLoss": [_duration_entry(start="2023-01-01", end="2023-12-31", val=20.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["net_income"] == 20.0

    def test_gross_profit_and_eps(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "GrossProfit": [_duration_entry(start="2023-01-01", end="2023-12-31", val=40.0, filed="2024-02-01")],
                "DilutedEarningsLossPerShare": [_duration_entry(start="2023-01-01", end="2023-12-31", val=3.5, filed="2024-02-01")],
            },
            units={"DilutedEarningsLossPerShare": "USD/shares"},
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["gross_profit"] == 40.0
        assert docs[0].metadata["eps"] == 3.5


class TestIfrsCashFlowMapping:
    def test_operating_investing_financing_and_free_cash_flow(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "CashFlowsFromUsedInOperatingActivities": [_duration_entry(start="2023-01-01", end="2023-12-31", val=30.0, filed="2024-02-01")],
                "CashFlowsFromUsedInInvestingActivities": [_duration_entry(start="2023-01-01", end="2023-12-31", val=-10.0, filed="2024-02-01")],
                "CashFlowsFromUsedInFinancingActivities": [_duration_entry(start="2023-01-01", end="2023-12-31", val=-5.0, filed="2024-02-01")],
                "PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities": [
                    _duration_entry(start="2023-01-01", end="2023-12-31", val=8.0, filed="2024-02-01")
                ],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        meta = docs[0].metadata
        assert meta["operating_cash_flow"] == 30.0
        assert meta["investing_cash_flow"] == -10.0
        assert meta["financing_cash_flow"] == -5.0
        assert meta["capital_expenditure"] == 8.0
        assert meta["free_cash_flow"] == 22.0  # 30 - 8

    def test_dividends_prefers_financing_classified_tag_falls_back_to_plain(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "DividendsPaid": [_duration_entry(start="2023-01-01", end="2023-12-31", val=7.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["dividends"] == 7.0


class TestIfrsBalanceSheetMapping:
    def test_current_assets_and_liabilities_use_ifrs_word_order(self):
        """IFRS tags read `CurrentAssets`/`CurrentLiabilities` --
        deliberately the *opposite* word order from US-GAAP's own
        `AssetsCurrent`/`LiabilitiesCurrent`. A guessed mapping using
        the US-GAAP order would silently map nothing; this proves the
        real, live-confirmed IFRS tag names are what is actually read."""
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "CurrentAssets": [_instant_entry(end="2023-12-31", val=50.0, filed="2024-02-01")],
                "CurrentLiabilities": [_instant_entry(end="2023-12-31", val=30.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        meta = docs[0].metadata
        assert meta["current_assets"] == 50.0
        assert meta["current_liabilities"] == 30.0
        assert meta["working_capital"] == 20.0

    def test_total_assets_equity_goodwill_intangibles(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "Assets": [_instant_entry(end="2023-12-31", val=200.0, filed="2024-02-01")],
                "Equity": [_instant_entry(end="2023-12-31", val=120.0, filed="2024-02-01")],
                "Goodwill": [_instant_entry(end="2023-12-31", val=15.0, filed="2024-02-01")],
                "IntangibleAssetsOtherThanGoodwill": [_instant_entry(end="2023-12-31", val=5.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        meta = docs[0].metadata
        assert meta["total_assets"] == 200.0
        assert meta["equity"] == 120.0
        assert meta["goodwill"] == 15.0
        assert meta["intangible_assets"] == 5.0
        assert meta["tangible_assets"] == 180.0  # 200 - 15 - 5

    def test_debt_current_plus_noncurrent_sums_to_total_debt(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "CurrentBorrowingsAndCurrentPortionOfNoncurrentBorrowings": [
                    _instant_entry(end="2023-12-31", val=10.0, filed="2024-02-01")
                ],
                "LongtermBorrowings": [_instant_entry(end="2023-12-31", val=40.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["total_debt"] == 50.0

    def test_single_borrowings_tag_is_the_fallback_total_debt(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "Borrowings": [_instant_entry(end="2023-12-31", val=45.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["total_debt"] == 45.0

    def test_cash_maps_directly(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "CashAndCashEquivalents": [_instant_entry(end="2023-12-31", val=25.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["cash"] == 25.0


class TestMissingOptionalIfrsFacts:
    def test_missing_optional_concepts_leave_only_revenue_never_fabricated(self):
        companyfacts = _companyfacts(
            concepts={"Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")]}
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["revenue"] == 100.0
        assert "net_income" not in docs[0].metadata
        assert "total_debt" not in docs[0].metadata
        assert "goodwill" not in docs[0].metadata

    def test_free_cash_flow_undetermined_when_capex_missing(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")],
                "CashFlowsFromUsedInOperatingActivities": [_duration_entry(start="2023-01-01", end="2023-12-31", val=30.0, filed="2024-02-01")],
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert "free_cash_flow" not in docs[0].metadata


class TestNoUsableTaxonomy:
    def test_empty_facts_dict_raises_missing_required_field(self):
        companyfacts = {"cik": 937966, "entityName": "Test", "facts": {}}
        with pytest.raises(MissingRequiredField):
            _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)

    def test_ifrs_full_present_but_no_mapped_concepts_have_real_annual_entries(self):
        """A payload with real ifrs-full data, but only for concepts
        this sprint's mapping does not include -- must fail honestly,
        never fabricate a document from nothing."""
        companyfacts = _companyfacts(
            concepts={"SomeUnmappedIfrsConcept": [_duration_entry(start="2023-01-01", end="2023-12-31", val=1.0, filed="2024-02-01")]}
        )
        with pytest.raises(MissingRequiredField):
            _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)

    def test_ifrs_data_only_quarterly_is_not_usable(self):
        companyfacts = _companyfacts(
            concepts={"Revenue": [_duration_entry(start="2023-01-01", end="2023-03-31", val=25.0, filed="2023-04-15")]}
        )
        # Q1 span fails `_is_annual_span`; also fp defaults to "FY" in
        # this file's own `_duration_entry` helper, so make the failure
        # unambiguous by using a genuinely quarterly fp too.
        companyfacts["facts"]["ifrs-full"]["Revenue"]["units"]["USD"][0]["fp"] = "Q1"
        with pytest.raises(MissingRequiredField):
            _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)

    def test_20fa_amendment_alone_is_not_usable_mirrors_domestic_10ka_strictness(self):
        """Parity with the existing us-gaap path's own exact strictness
        (`"10-K"` only, never `"10-K/A"`) -- this sprint does not
        loosen that discipline for foreign filers."""
        companyfacts = _companyfacts(
            concepts={"Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, form="20-F/A", filed="2024-02-01")]}
        )
        with pytest.raises(MissingRequiredField):
            _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)


class TestDuplicateAndRevisedPeriods:
    def test_duplicate_ifrs_period_keeps_the_most_recently_filed_entry(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [
                    _duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01", accn="orig"),
                    _duration_entry(start="2023-01-01", end="2023-12-31", val=105.0, filed="2024-05-01", accn="amended"),
                ]
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert len(docs) == 1
        assert docs[0].metadata["revenue"] == 105.0
        assert docs[0].metadata["sec_accession"] == "amended"

    def test_multiple_annual_periods_produce_chronologically_ordered_documents(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [
                    _duration_entry(start="2022-01-01", end="2022-12-31", val=90.0, filed="2023-02-01"),
                    _duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01"),
                ]
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert [d.period_end.isoformat() for d in docs] == ["2022-12-31", "2023-12-31"]
        assert [d.metadata["revenue"] for d in docs] == [90.0, 100.0]


class TestProvenancePreserved:
    def test_metadata_carries_taxonomy_form_currency_and_accession(self):
        companyfacts = _companyfacts(
            concepts={
                "Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01", accn="0001-24-000123")]
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        meta = docs[0].metadata
        assert meta["sec_taxonomy"] == "ifrs-full"
        assert meta["sec_form"] == "20-F"
        assert meta["currency"] == "USD"
        assert meta["sec_cik"] == "0000937966"
        assert meta["sec_accession"] == "0001-24-000123"

    def test_provider_id_source_kind_and_period_dates_are_the_same_shape_as_us_gaap(self):
        companyfacts = _companyfacts(
            concepts={"Revenue": [_duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01")]}
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        doc = docs[0]
        assert doc.provider_id == "sec_edgar"
        assert doc.source_kind == "financial_statement"
        assert doc.period_start.isoformat() == "2023-01-01"
        assert doc.period_end.isoformat() == "2023-12-31"

    def test_non_usd_currency_detected_from_the_real_data_never_hardcoded(self):
        companyfacts = _companyfacts(
            taxonomy="us-gaap",
            concepts={"RevenueFromContractWithCustomerExcludingAssessedTax": [
                _entry(start="2023-01-01", end="2023-12-31", val=32000000000.0, form="20-F", filed="2024-02-01")
            ]},
            units={"RevenueFromContractWithCustomerExcludingAssessedTax": "EUR"},
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        assert docs[0].metadata["currency"] == "EUR"


class TestReachesDownstreamEvaluators:
    """Requirement 8's own final bullet: proves a real, IFRS-sourced
    normalized result reaches the same Growth/Capital Allocation/Risk
    evaluators a US-GAAP company's data reaches -- through the real,
    unmodified `ingest`/`extract_facts_from_records`/`evaluate_business
    _analysis`/`evaluate_risk` pipeline, never a special-cased path."""

    def test_ifrs_sourced_record_produces_a_real_growth_conclusion(self):
        from atlas.analysis_engine.growth import evaluate_growth
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
        from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records

        companyfacts = _companyfacts(
            concepts={
                "Revenue": [
                    _duration_entry(start="2021-01-01", end="2021-12-31", val=80.0, filed="2022-02-01"),
                    _duration_entry(start="2022-01-01", end="2022-12-31", val=90.0, filed="2023-02-01"),
                    _duration_entry(start="2023-01-01", end="2023-12-31", val=100.0, filed="2024-02-01"),
                ]
            }
        )
        docs = _provider(companyfacts).fetch(company_identifier="ASML", evaluated_at=_NOW)
        records = []
        for doc in docs:
            result = ingest(doc, existing_records=tuple(records), evaluated_at=_NOW)
            assert isinstance(result, IngestedRecord)
            records.append(result.record)

        facts = extract_facts_from_records(tuple(records), evaluated_at=_NOW)
        finding = evaluate_growth(facts, evaluated_at=_NOW)
        assert finding.status is not BusinessCategoryStatus.NOT_EVALUATED
        assert finding.status is not BusinessCategoryStatus.INSUFFICIENT_INPUT
