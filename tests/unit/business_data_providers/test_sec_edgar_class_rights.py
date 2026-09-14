"""Class economic-rights evidence (Issuer Common-Equity Market Cap v1).

Real controls are trimmed copies of the ten filings the sprint's SEC plan
fetched (`fixtures/class_rights/<accession>.xml`: dei facts, cover rows,
per-class EPS, conversion and as-converted facts, preferred facts, one share
fact per class member, and only the text-block sentences the parser keeps);
each trimmed copy was checked to parse identically to the full instance.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

from atlas.business_data_providers.sec_edgar_class_rights import (
    EvidenceStrength,
    RightKind,
    SecEdgarClassRightsProvider,
    parse_class_rights,
)
from tests.unit.business_data_providers.test_sec_edgar_share_classes import _code_without_docstrings, _instance

FIXTURES = Path(__file__).parent / "fixtures" / "class_rights"
MODULE = Path(__file__).resolve().parents[3] / "atlas" / "business_data_providers" / "sec_edgar_class_rights.py"
A, B, C = "us-gaap:CommonClassAMember", "us-gaap:CommonClassBMember", "us-gaap:CommonClassCMember"
GOOG_C = "goog:CapitalClassCMember"


def _read(accession):
    return parse_class_rights((FIXTURES / f"{accession}.xml").read_text())


def _facts(filing, kind):
    return [f for f in filing.facts if f.kind is kind]


class TestAlphabet:
    def test_parity_under_the_certificate_of_incorporation_is_contractual(self):
        parity = _facts(_read("0001652044-26-000018"), RightKind.ECONOMIC_PARITY)
        cited = [f for f in parity if f.strength is EvidenceStrength.CONTRACTUAL]
        assert len(cited) == 1 and set(cited[0].related_members) == {A, B, GOOG_C}
        assert "certificate of incorporation" in cited[0].excerpt
        assert (cited[0].effective_from, cited[0].effective_to) == (date(2023, 1, 1), date(2025, 12, 31))

    def test_an_earlier_statement_without_the_citation_is_a_filing_statement(self):
        parity = _facts(_read("0001652044-23-000016"), RightKind.ECONOMIC_PARITY)
        assert {f.strength for f in parity} == {EvidenceStrength.FILING_STATEMENT}
        assert ("*",) in {f.related_labels for f in parity}  # "each class of our common and capital stock"

    def test_class_b_converts_into_class_a_ratio_unstated_and_votes_differ(self):
        filing = _read("0001652044-26-000018")
        (conversion,) = _facts(filing, RightKind.CONVERTIBLE_INTO)
        assert (conversion.subject_member, conversion.target_member, conversion.value) == (B, A, None)
        assert {(f.subject_member, f.value) for f in _facts(filing, RightKind.VOTES_PER_SHARE)} == {(A, 1.0), (B, 10.0)}

    def test_class_c_resolves_through_its_own_cover_title_and_the_standard_member(self):
        (parity,) = _facts(_read("0001652044-26-000071"), RightKind.ECONOMIC_PARITY)
        assert {GOOG_C, C} <= set(parity.related_members)

    def test_per_class_eps_is_accounting_corroboration_never_contractual(self):
        eps = _facts(_read("0001652044-26-000018"), RightKind.EARNINGS_PER_SHARE)
        assert {f.strength for f in eps} == {EvidenceStrength.ACCOUNTING_CORROBORATION}
        fy2025 = {f.subject_member: f.value for f in eps if f.effective_to == date(2025, 12, 31)}
        assert fy2025 == {A: 10.91, B: 10.91, GOOG_C: 10.91}

    def test_the_mandatory_convertible_preferred_is_senior_structured_evidence(self):
        filing = _read("0001652044-26-000071")
        outstanding = {f.effective_to: f.value for f in _facts(filing, RightKind.PREFERRED_SHARES_OUTSTANDING) if not f.subject_member}
        assert outstanding == {date(2025, 12, 31): 0.0, date(2026, 6, 30): 19_000_000.0}
        ranges = {(f.value_low, f.value_high) for f in _facts(filing, RightKind.CONVERSION_RATIO_RANGE)}
        assert ranges == {(2.252, 2.816), (2.274, 2.842)}
        assert 0.0625 in {f.value for f in _facts(filing, RightKind.PREFERRED_DIVIDEND_RATE)}
        assert 1000.0 in {f.value for f in _facts(filing, RightKind.LIQUIDATION_PREFERENCE)}


class TestMastercardAndMeta:
    def test_mastercard_class_b_is_non_voting_and_converts_one_for_one(self):
        filing = _read("0001141391-26-000013")
        (conversion,) = _facts(filing, RightKind.CONVERTIBLE_INTO)
        assert (conversion.subject_member, conversion.target_member, conversion.value) == (B, A, 1.0)
        assert [f.subject_member for f in _facts(filing, RightKind.NON_VOTING)] == [B]
        assert _facts(filing, RightKind.EARNINGS_PER_SHARE) == []  # MA reports no per-class EPS

    def test_meta_parity_names_both_classes(self):
        (parity,) = _facts(_read("0001628280-26-050705"), RightKind.ECONOMIC_PARITY)
        assert set(parity.related_members) == {A, B} and parity.strength is EvidenceStrength.FILING_STATEMENT


class TestVisa:
    def test_conversion_rates_at_each_period_end_and_zero_is_not_a_rate(self):
        filing = _read("0001403161-26-000104")
        rates = {(f.subject_member, f.effective_to): f.value for f in _facts(filing, RightKind.CONVERSION_RATE)}
        assert rates[(C, date(2026, 6, 30))] == 4.0
        assert rates[("v:CommonClassB1Member", date(2026, 6, 30))] == 1.5445
        assert rates[("v:CommonClassB3Member", date(2026, 6, 30))] == 1.4953
        assert (A, date(2026, 6, 30)) not in rates  # reported as 0: the numeraire has no rate

    def test_historical_rates_come_from_their_own_instants(self):
        rates = {(f.subject_member, f.effective_to): f.value for f in _facts(_read("0001403161-22-000081"), RightKind.CONVERSION_RATE)}
        assert rates[(B, date(2021, 9, 30))] == 1.6228 and rates[(B, date(2022, 9, 30))] == 1.6059

    def test_as_converted_counts_include_participating_preferred_and_the_issuer_total(self):
        facts = _facts(_read("0001403161-26-000104"), RightKind.AS_CONVERTED_SHARES)
        at = {f.subject_member: f.value for f in facts if f.effective_to == date(2026, 6, 30) and f.concept.endswith("SharesOutstandingAsConvertedBasis")}
        assert at[A] == 1_702_000_000 and at[None] == 1_880_000_000
        assert at["us-gaap:SeriesBPreferredStockMember"] == 1_000_000

    def test_inventory_tells_common_from_preferred(self):
        inventory = {f.subject_member: f.equity_kind for f in _facts(_read("0001403161-26-000104"), RightKind.CLASS_INVENTORY)}
        assert inventory[A] == inventory["v:CommonClassB3Member"] == "common"
        assert inventory["us-gaap:SeriesCPreferredStockMember"] == "preferred"


class TestVistraPreferred:
    def test_senior_non_convertible_preferred_with_filed_rates(self):
        filing = _read("0001692819-26-000019")
        assert {f.equity_kind for f in _facts(filing, RightKind.CLASS_INVENTORY)} == {"preferred"}
        rates = {f.subject_member: f.value for f in _facts(filing, RightKind.PREFERRED_DIVIDEND_RATE)
                 if f.strength is EvidenceStrength.STRUCTURED_FILING and f.subject_member}
        assert rates == {"us-gaap:SeriesAPreferredStockMember": 0.08, "us-gaap:SeriesBPreferredStockMember": 0.07,
                         "us-gaap:SeriesCPreferredStockMember": 0.08875}
        assert _facts(filing, RightKind.NOT_CONVERTIBLE) and _facts(filing, RightKind.SENIOR_TO_COMMON)
        outstanding = {f.subject_member: f.value for f in _facts(filing, RightKind.PREFERRED_SHARES_OUTSTANDING)
                       if f.strength is EvidenceStrength.STRUCTURED_FILING and f.subject_member}
        issued = {f.subject_member: f.value for f in _facts(filing, RightKind.PREFERRED_SHARES_ISSUED) if f.subject_member}
        assert outstanding["us-gaap:SeriesCPreferredStockMember"] == 476_066 != issued["us-gaap:SeriesCPreferredStockMember"]


class TestSynthetic:
    def _text(self, sentence, rows=()):
        block = ('<us-gaap:StockholdersEquityNoteDisclosureTextBlock contextRef="FY">&lt;p&gt;' + sentence
                 + '&lt;/p&gt;</us-gaap:StockholdersEquityNoteDisclosureTextBlock>')
        income = '<us-gaap:NetIncomeLoss contextRef="FY" unitRef="usd" decimals="-6">1000000</us-gaap:NetIncomeLoss>'
        return parse_class_rights(_instance(rows=rows).replace("</xbrli:xbrl>", income + block + "</xbrli:xbrl>"))

    def test_an_unmatched_sentence_yields_nothing(self):
        assert self._text("Class B holders enjoy the annual meeting.").facts == ()

    def test_a_certificate_citation_makes_parity_contractual(self):
        (f,) = self._text("Under our certificate of incorporation the rights of Class A and Class B stock are identical, "
                          "except with respect to voting.").facts
        assert f.strength is EvidenceStrength.CONTRACTUAL and f.related_labels == ("Class A", "Class B")
        assert set(f.related_members) == set()  # no such member used in this filing: nothing resolved

    def test_the_subject_is_the_class_named_last_before_the_verb(self):
        (f,) = self._text("Dividends were paid on Class A stock. Class B Conversions Shares of Class B common stock are "
                          "convertible on a one-for-one basis into shares of Class A common stock.").facts
        assert (f.subject_label, f.target_label, f.value) == ("Class B", "Class A", 1.0)

    def test_labels_resolve_only_through_the_filings_own_cover_titles(self):
        rows = [("r1", "abc:SpecialMember", "Class Z Special Stock", "ZZZ", "NASDAQ")]
        facts = self._text("The rights of Class Z and Class Y stock are identical, except with respect to voting.", rows).facts
        (f,) = [x for x in facts if x.kind is RightKind.ECONOMIC_PARITY]
        assert f.related_members == ("abc:SpecialMember",)  # Class Y: no member of its own anywhere


class TestFetching:
    def test_one_request_to_a_recorded_edgar_instance_only(self):
        calls, counted = [], []
        provider = SecEdgarClassRightsProvider(lambda url, headers: calls.append(url) or "<xbrl/>")
        url = "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/x_htm.xml"
        assert provider.fetch_instance_at(instance_url=url, on_request=lambda: counted.append(1)) == "<xbrl/>"
        assert calls == [url] and counted == [1]
        with pytest.raises(ValueError):
            provider.fetch_instance_at(instance_url="https://example.com/x.xml")


def test_the_adapter_names_no_issuer_symbol_or_class():
    code = _code_without_docstrings(MODULE)
    for name in ("GOOG", "GOOGL", "MA", "V", "META", "VST", "Alphabet", "Visa", "Mastercard", "Vistra"):
        assert not re.search(rf"\b{name}\b", code), name
    assert not re.search(r"CommonClass[A-Z]Member|Class[A-Z]\d", code.replace("CommonClass{letter}Member", ""))
