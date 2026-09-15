"""Class economic-rights evidence (Issuer Common-Equity Market Cap v1).

Real controls are trimmed copies of the ten filings the sprint's SEC plan
fetched (`fixtures/class_rights/<accession>.xml`: dei facts, cover rows,
per-class EPS, conversion and as-converted facts, preferred facts, one share
fact per class member, and only the text-block sentences the parser keeps);
each trimmed copy was checked to parse identically to the full instance.
AMD's and Moody's 10-Qs (`0000002488-26-000123`, `0001628280-26-049398`)
were added by the class-inventory plan: every dei fact, every share fact,
the income facts that date the presented period, and their contexts --
checked to parse identically under the class-rights, cover and share-class
parsers.
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
from atlas.business_data_providers.sec_edgar_share_classes import parse_cover_share_counts
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


class TestClassAxisShareFacts:
    """Which member, on which concept and context, made a filing "report share
    classes" -- kept fact by fact, never reduced to the boolean. AMD's and
    Moody's 10-Qs are real controls (`0000002488-26-000123`,
    `0001628280-26-049398`)."""

    @staticmethod
    def _axis(filing):
        return _facts(filing, RightKind.CLASS_AXIS_SHARE_FACT)

    def test_every_class_axis_share_fact_is_kept_with_its_provenance(self):
        axis = self._axis(_read("0001628280-26-049398"))
        at = {(f.subject_member, f.concept, f.effective_to): (f.value, f.context_id, f.equity_kind) for f in axis}
        series, non_series = "mco:SeriesCommonStockMember", "mco:NonSeriesCommonStockMember"
        assert at[(series, "us-gaap:CommonStockSharesOutstanding", date(2026, 6, 30))] == (0.0, "c-11", "common")
        assert at[(series, "us-gaap:CommonStockSharesIssued", date(2026, 6, 30))] == (0.0, "c-11", "common")
        assert at[(non_series, "us-gaap:CommonStockSharesIssued", date(2026, 6, 30))] == (342_902_272.0, "c-12", "common")
        # Authorized shares count nothing outstanding: kept, of no equity kind.
        assert at[(non_series, "us-gaap:CommonStockSharesAuthorized", date(2026, 6, 30))] == (1_000_000_000.0, "c-12", None)
        assert len(axis) == 10 and {f.unit for f in axis} == {"shares"}
        assert {f.strength for f in axis} == {EvidenceStrength.STRUCTURED_FILING}

    def test_the_members_behind_the_boolean_are_exactly_the_facts_kept(self):
        for accession in ("0000002488-26-000123", "0001628280-26-049398"):
            text = (FIXTURES / f"{accession}.xml").read_text()
            assert parse_cover_share_counts(text).share_classes_reported
            member_of = {m.group(1): m.group(2) for m in re.finditer(
                r'<context id="([^"]+)">(?:(?!</context>).)*?dimension="us-gaap:StatementClassOfStockAxis">([^<]+)<', text, re.S)}
            share_contexts = {re.search(r'contextRef="([^"]+)"', tag).group(1)
                              for tag in re.findall(r'<[^>]*unitRef="shares"[^>]*>', text)}
            axis = self._axis(_read(accession))
            assert {f.subject_member for f in axis} == {member_of[c] for c in share_contexts if c in member_of}, accession
            assert {f.context_id for f in axis} == share_contexts & set(member_of)

    def test_amds_flag_is_the_generic_common_member_on_incidental_concepts_too(self):
        axis = self._axis(_read("0000002488-26-000123"))
        assert {f.subject_member for f in axis} == {"us-gaap:CommonStockMember"}
        counts = {f.effective_to: f.value for f in axis if f.concept == "us-gaap:CommonStockSharesIssued"}
        assert counts[date(2026, 6, 27)] == 1_632_000_000.0
        incidental = {f.concept for f in axis if f.equity_kind is None}
        assert "us-gaap:StockRepurchasedDuringPeriodShares" in incidental
        spans = {(f.effective_from, f.effective_to) for f in axis if f.concept == "us-gaap:StockRepurchasedDuringPeriodShares"}
        assert (date(2026, 3, 29), date(2026, 6, 27)) in spans  # a duration: its own period, never an instant

    def test_a_further_dimension_is_kept_beside_the_member(self):
        extra = ('<xbrli:context id="two"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001'
                 '</xbrli:identifier><xbrli:segment><xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">'
                 'abc:SeriesXMember</xbrldi:explicitMember><xbrldi:explicitMember dimension="dei:LegalEntityAxis">'
                 'abc:SubsidiaryMember</xbrldi:explicitMember></xbrli:segment></xbrli:entity><xbrli:period>'
                 '<xbrli:instant>2025-12-31</xbrli:instant></xbrli:period></xbrli:context>')
        fact = '<us-gaap:CommonStockSharesOutstanding contextRef="two" unitRef="shares" decimals="0">0</us-gaap:CommonStockSharesOutstanding>'
        text = _instance(facts=[("us-gaap:CommonStockSharesOutstanding", "abc:ClassXMember", "2025-12-31", "5000", "shares")],
                         extra_contexts=extra).replace("</xbrli:xbrl>", fact + "</xbrli:xbrl>")
        axis = {f.subject_member: f for f in _facts(parse_class_rights(text), RightKind.CLASS_AXIS_SHARE_FACT)}
        assert axis["abc:SeriesXMember"].related_labels == ("dei:LegalEntityAxis=abc:SubsidiaryMember",)
        assert (axis["abc:ClassXMember"].related_labels, axis["abc:ClassXMember"].value) == ((), 5000.0)

    def test_monetary_and_undimensioned_facts_are_not_class_axis_share_facts(self):
        text = _instance(facts=[("us-gaap:CommonStockSharesOutstanding", None, "2025-12-31", "9000", "shares"),
                                ("us-gaap:CommonStockValue", "abc:ClassXMember", "2025-12-31", "90", "usd")])
        assert _facts(parse_class_rights(text), RightKind.CLASS_AXIS_SHARE_FACT) == []


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
    for name in ("GOOG", "GOOGL", "MA", "V", "META", "VST", "AMD", "MCO", "Alphabet", "Visa", "Mastercard", "Vistra",
                 "Moody", "mco", "amd"):
        assert not re.search(rf"\b{name}\b", code), name
    assert not re.search(r"CommonClass[A-Z]Member|Class[A-Z]\d", code.replace("CommonClass{letter}Member", ""))
