"""Current cover-page share counts (Current Share-Count Evidence v1).

Real controls are trimmed copies of each corpus filer's latest 10-K/10-Q
instance (`fixtures/cover_shares/<accession>.xml`: every cover row, cover
count and entity-wide fact the parser reads, one share fact per reported
class member, and period-end/weighted-average decoys it must not read),
fetched once from EDGAR; the trim was checked to parse identically to the
full instance. Synthetic instances cover what no real filing exercised.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

from atlas.business_data_providers.sec_edgar_share_classes import (
    COVER_SHARE_CONCEPTS,
    CountScope,
    LinkKind,
    SecEdgarShareClassProvider,
    latest_periodic_filing,
    parse_cover_share_counts,
    submissions_url,
)
from tests.unit.business_data_providers.test_sec_edgar_share_classes import MODULE, _code_without_docstrings, _instance

FIXTURES = Path(__file__).parent / "fixtures" / "cover_shares"
PROVEN, AMBIGUOUS, NO_LINK = LinkKind.PROVEN_BY_SHARED_DIMENSION, LinkKind.AMBIGUOUS, LinkKind.NO_LINK
CLASS_A, CLASS_B, CLASS_C = "us-gaap:CommonClassAMember", "us-gaap:CommonClassBMember", "us-gaap:CommonClassCMember"
COVER = "dei:EntityCommonStockSharesOutstanding"
PERIOD_END = "us-gaap:CommonStockSharesOutstanding"

#: accession -> (CIK, form, document period end, [(member, as of, shares, link, symbol)]).
READINGS = {
    "0000002488-26-000123": ("0000002488", "10-Q", "2026-06-27", [(None, "2026-07-29", 1_632_475_042, AMBIGUOUS, None)]),
    "0000018230-26-000046": ("0000018230", "10-Q", "2026-06-30", [(None, "2026-06-30", 459_674_889, AMBIGUOUS, None)]),
    "0000100885-26-000250": ("0000100885", "10-Q", "2026-06-30", [(None, "2026-07-17", 594_075_498, PROVEN, "UNP")]),
    "0000320193-26-000020": ("0000320193", "10-Q", "2026-06-27", [(None, "2026-07-17", 14_594_180_000, AMBIGUOUS, None)]),
    "0000723125-26-000015": ("0000723125", "10-Q", "2026-05-28", [(None, "2026-06-17", 1_129_393_151, PROVEN, "MU")]),
    "0001018724-26-000026": ("0001018724", "10-Q", "2026-06-30", [(None, "2026-07-22", 10_786_313_572, AMBIGUOUS, None)]),
    "0001045810-26-000075": ("0001045810", "10-Q", "2026-07-26", [(None, "2026-08-21", 24_100_000_000, PROVEN, "NVDA")]),
    "0001104659-26-102213": ("0000315189", "10-Q", "2026-08-02", [(None, "2026-08-02", 269_625_412, AMBIGUOUS, None)]),
    "0001108524-26-000190": ("0001108524", "10-Q", "2026-07-31", [(None, "2026-08-20", 823_000_000, PROVEN, "CRM")]),
    "0001141391-26-000083": ("0001141391", "10-Q", "2026-06-30", [
        (CLASS_A, "2026-07-27", 869_464_115, PROVEN, "MA"), (CLASS_B, "2026-07-27", 6_545_825, NO_LINK, None)]),
    "0001193125-26-323660": ("0000789019", "10-K", "2026-06-30", [(None, "2026-07-23", 7_425_545_491, AMBIGUOUS, None)]),
    "0001403161-26-000104": ("0001403161", "10-Q", "2026-06-30", [
        (CLASS_A, "2026-07-21", 1_704_112_694, PROVEN, "V"), (CLASS_C, "2026-07-21", 17_059_152, NO_LINK, None),
        ("v:CommonClassB1Member", "2026-07-21", 2_180_148, NO_LINK, None),
        ("v:CommonClassB2Member", "2026-07-21", 486_669, NO_LINK, None),
        ("v:CommonClassB3Member", "2026-07-21", 60_589_871, NO_LINK, None)]),
    "0001535527-26-000031": ("0001535527", "10-Q", "2026-07-31", [(None, "2026-08-20", 1_023_934_842, AMBIGUOUS, None)]),
    "0001628280-26-049270": ("0001318605", "10-Q", "2026-06-30", [(None, "2026-07-16", 3_949_547_394, PROVEN, "TSLA")]),
    "0001628280-26-049398": ("0001059556", "10-Q", "2026-06-30", [(None, "2026-06-30", 173_200_000, AMBIGUOUS, None)]),
    "0001628280-26-050705": ("0001326801", "10-Q", "2026-06-30", [
        (CLASS_A, "2026-07-24", 2_205_128_509, AMBIGUOUS, None), (CLASS_B, "2026-07-24", 342_377_716, AMBIGUOUS, None)]),
    "0001628280-26-058235": ("0000006951", "10-Q", "2026-07-26", [(None, "2026-07-26", 793_597_443, PROVEN, "AMAT")]),
    "0001652044-26-000071": ("0001652044", "10-Q", "2026-06-30", [
        ("goog:CapitalClassCMember", "2026-07-15", 5_527_000_000, PROVEN, "GOOG"),
        (CLASS_A, "2026-07-15", 5_868_000_000, PROVEN, "GOOGL"), (CLASS_B, "2026-07-15", 835_000_000, NO_LINK, None)]),
    "0001692819-26-000019": ("0001692819", "10-Q", "2026-06-30", [(None, "2026-08-03", 335_635_195, AMBIGUOUS, None)]),
}


def _read(accession: str):
    return parse_cover_share_counts((FIXTURES / f"{accession}.xml").read_text())


def _cover_instance(*, rows=(), facts=(), extra_contexts="", doc_type="10-Q"):
    return _instance(rows=rows, facts=facts, extra_contexts=extra_contexts).replace(
        '<dei:DocumentType contextRef="FY">10-K</dei:DocumentType>',
        f'<dei:DocumentType contextRef="FY">{doc_type}</dei:DocumentType>')


# -- real controls ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("accession", sorted(READINGS))
def test_every_corpus_filing_reads_as_pinned(accession):
    cik, form, period_end, expected = READINGS[accession]
    filing = _read(accession)
    assert (filing.entity_cik, filing.document_type, filing.amendment, filing.document_period_end) == (
        cik, form, False, date.fromisoformat(period_end))
    got = [(c.class_member, c.as_of.isoformat(), c.shares, c.link_kind, c.cover.symbol if c.cover else None)
           for c in filing.counts]
    assert sorted(got, key=str) == sorted([(m, a, float(s), k, sym) for m, a, s, k, sym in expected], key=str)
    assert all(c.scope is (CountScope.ISSUER if c.class_member is None else CountScope.CLASS) for c in filing.counts)
    assert not any(c.conflict for c in filing.counts)


def test_the_as_of_date_is_the_counts_own_instant():
    """CRM's cover count is dated 2026-08-20: neither the quarter end
    (2026-07-31) nor the filing date (2026-08-27)."""
    filing = _read("0001108524-26-000190")
    (count,) = filing.counts
    assert count.as_of == date(2026, 8, 20) != filing.document_period_end


def test_the_reported_precision_is_kept():
    """A rounded cover count says so: NVDA's is rounded to 100M, CRM's and
    Alphabet's to the million, UNP's is exact."""
    decimals = {a: {c.decimals for c in _read(a).counts} for a in READINGS}
    assert decimals["0001045810-26-000075"] == {"-8"}
    assert decimals["0001108524-26-000190"] == decimals["0001652044-26-000071"] == {"-6"}
    assert decimals["0000100885-26-000250"] == {"INF"}


def test_period_end_and_weighted_average_decoys_are_never_cover_counts():
    for accession in READINGS:
        text = (FIXTURES / f"{accession}.xml").read_text()
        assert PERIOD_END in text or "WeightedAverageNumberOfSharesOutstandingBasic" in text, accession
        assert {c.concept for c in _read(accession).counts} == set(COVER_SHARE_CONCEPTS)


class TestMultiClass:
    def test_alphabet_class_c_is_goog_class_a_is_googl_class_b_is_neither(self):
        counts = {c.class_member: c for c in _read("0001652044-26-000071").counts}
        assert (counts["goog:CapitalClassCMember"].cover.symbol, counts[CLASS_A].cover.symbol) == ("GOOG", "GOOGL")
        assert counts[CLASS_B].link_kind is NO_LINK and counts[CLASS_B].cover is None
        assert not [c for c in counts.values() if c.scope is CountScope.ISSUER]  # no issuer total is invented

    def test_mastercard_class_b_and_visa_b_series_never_link(self):
        for accession, listed in (("0001141391-26-000083", "MA"), ("0001403161-26-000104", "V")):
            counts = _read(accession).counts
            assert [c.cover.symbol for c in counts if c.link_kind is PROVEN] == [listed]
            assert all(c.cover is None for c in counts if c.class_member != CLASS_A)

    @pytest.mark.parametrize("accession", ["0001628280-26-050705", "0001535527-26-000031"])
    def test_an_undimensioned_row_beside_reported_classes_proves_nothing(self, accession):
        """META (classes on the cover counts) and CRWD (one undimensioned
        count, classes reported elsewhere): the single §12(b) row is never
        assigned to a class or to the total."""
        filing = _read(accession)
        assert filing.share_classes_reported and len(filing.cover_rows) == 1
        assert {c.link_kind for c in filing.counts} == {AMBIGUOUS}


class TestTheStrictRuleKnownGap:
    """Single-class filers the same-filing rule cannot prove today: the
    common §12(b) row is class-dimensioned while the count is not, or share
    facts carry class members, or the row carries another dimension. Pinned
    so that a generic rule change is visible, never silent."""

    @pytest.mark.parametrize("accession", [
        "0000320193-26-000020", "0001018724-26-000026", "0000018230-26-000046", "0001104659-26-102213",
        "0001193125-26-323660", "0001628280-26-049398"])
    def test_a_member_dimensioned_common_row_does_not_share_the_default_dimension(self, accession):
        filing = _read(accession)
        assert [c.link_kind for c in filing.counts] == [AMBIGUOUS]
        assert not [r for r in filing.cover_rows if r.class_member is None]

    def test_a_row_with_another_dimension_is_not_the_default_row(self):
        filing = _read("0001692819-26-000019")
        assert [r.other_dimensions for r in filing.cover_rows] == [1] and filing.counts[0].link_kind is AMBIGUOUS


# -- synthetic ----------------------------------------------------------------------------------------------


class TestSyntheticLinking:
    def test_one_undimensioned_listed_row_and_no_classes_proves_the_issuer_count(self):
        filing = parse_cover_share_counts(_cover_instance(
            rows=[("r0", None, "Common", "AAA", "NASDAQ")], facts=[(COVER, None, "2026-07-20", 500, "shares")]))
        (count,) = filing.counts
        assert (count.scope, count.link_kind, count.cover.symbol, count.as_of, count.shares) == (
            CountScope.ISSUER, PROVEN, "AAA", date(2026, 7, 20), 500.0)

    def test_any_reported_class_makes_the_undimensioned_count_ambiguous(self):
        filing = parse_cover_share_counts(_cover_instance(
            rows=[("r0", None, "Common", "AAA", "NASDAQ")],
            facts=[(COVER, None, "2026-07-20", 500, "shares"), (PERIOD_END, "abc:ClassBMember", "2025-12-31", 5, "shares")]))
        assert filing.share_classes_reported and filing.counts[0].link_kind is AMBIGUOUS

    def test_no_cover_row_is_no_link_and_an_unlisted_row_is_ambiguous(self):
        assert parse_cover_share_counts(_cover_instance(
            facts=[(COVER, None, "2026-07-20", 500, "shares")])).counts[0].link_kind is NO_LINK
        for row in [("r0", None, "Common", "AAA", "NASDAQ", "true"), ("r0", None, "Common", "AAA", None)]:
            filing = parse_cover_share_counts(_cover_instance(rows=[row], facts=[(COVER, None, "2026-07-20", 5, "shares")]))
            assert filing.counts[0].link_kind is AMBIGUOUS

    def test_a_second_row_claiming_the_same_listing_is_a_rival(self):
        filing = parse_cover_share_counts(_cover_instance(
            rows=[("r0", None, "Common", "AAA", "NASDAQ"), ("rn", "abc:NotesMember", "Notes", "AAA", "NASDAQ")],
            facts=[(COVER, None, "2026-07-20", 500, "shares")]))
        assert filing.counts[0].link_kind is AMBIGUOUS

    def test_class_counts_link_by_their_own_member_only(self):
        filing = parse_cover_share_counts(_cover_instance(
            rows=[("ra", CLASS_A, "Class A", "AAA", "NASDAQ"), ("rc", "abc:ClassCMember", "Class C", "AAC", "NASDAQ")],
            facts=[(COVER, CLASS_A, "2026-07-20", 10, "shares"), (COVER, "abc:ClassCMember", "2026-07-20", 30, "shares"),
                   (COVER, CLASS_B, "2026-07-20", 2, "shares")]))
        links = {c.class_member: (c.link_kind, c.cover.symbol if c.cover else None, c.shares) for c in filing.counts}
        assert links == {CLASS_A: (PROVEN, "AAA", 10.0), "abc:ClassCMember": (PROVEN, "AAC", 30.0), CLASS_B: (NO_LINK, None, 2.0)}

    def test_disagreeing_values_for_one_scope_and_date_are_a_conflict(self):
        filing = parse_cover_share_counts(_cover_instance(
            rows=[("r0", None, "Common", "AAA", "NASDAQ")],
            facts=[(COVER, None, "2026-07-20", 500, "shares"), (COVER, None, "2026-07-20", 501, "shares")]))
        (count,) = filing.counts
        assert count.conflict and count.shares is None

    def test_two_dates_are_two_counts_each_with_its_own_date(self):
        filing = parse_cover_share_counts(_cover_instance(
            rows=[("r0", None, "Common", "AAA", "NASDAQ")],
            facts=[(COVER, None, "2026-07-20", 500, "shares"), (COVER, None, "2026-06-30", 490, "shares")]))
        assert [(c.as_of, c.shares) for c in filing.counts] == [(date(2026, 6, 30), 490.0), (date(2026, 7, 20), 500.0)]

    def test_zero_and_negative_counts_are_read_as_reported_and_left_to_eligibility(self):
        for value in (0, -5):
            filing = parse_cover_share_counts(_cover_instance(
                rows=[("r0", None, "Common", "AAA", "NASDAQ")], facts=[(COVER, None, "2026-07-20", value, "shares")]))
            assert filing.counts[0].shares == float(value)

    def test_other_units_further_dimensions_and_period_end_counts_are_not_cover_counts(self):
        extra = ('<xbrli:context id="x2"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001'
                 '</xbrli:identifier><xbrli:segment>'
                 '<xbrldi:explicitMember dimension="dei:EntityListingsExchangeAxis">abc:X</xbrldi:explicitMember>'
                 '</xbrli:segment></xbrli:entity><xbrli:period><xbrli:instant>2026-07-20</xbrli:instant></xbrli:period></xbrli:context>')
        text = _cover_instance(
            rows=[("r0", None, "Common", "AAA", "NASDAQ")], extra_contexts=extra,
            facts=[(COVER, None, "2026-07-20", 500, "usd"), (PERIOD_END, None, "2026-06-30", 480, "shares")],
        ).replace("</xbrli:xbrl>", f'<{COVER} contextRef="x2" unitRef="shares" decimals="0">7</{COVER}></xbrli:xbrl>')
        assert parse_cover_share_counts(text).counts == ()


# -- locating filings (submissions are never evidence) ------------------------------------------------------


def _submissions(*rows):
    keys = ("accessionNumber", "form", "filingDate", "reportDate")
    return {"filings": {"recent": {k: [r[i] for r in rows] for i, k in enumerate(keys)}}}


class TestLatestPeriodicFiling:
    ROWS = (
        ("0000000001-26-000009", "8-K", "2026-09-01", ""),
        ("0000000001-26-000008", "10-Q/A", "2026-08-30", "2026-06-30"),
        ("0000000001-26-000007", "10-Q", "2026-08-05", "2026-06-30"),
        ("0000000001-26-000004", "10-K", "2026-02-05", "2025-12-31"),
        ("0000000001-26-000010", "10-Q", "2026-11-04", "2026-09-30"),
    )

    def test_the_latest_original_10q_or_10k_filed_by_the_date(self):
        found = latest_periodic_filing(_submissions(*self.ROWS), filed_by=date(2026, 9, 14))
        assert (found.accession, found.form, found.filing_date, found.report_date) == (
            "0000000001-26-000007", "10-Q", date(2026, 8, 5), date(2026, 6, 30))

    def test_a_filing_after_the_date_is_invisible(self):
        assert latest_periodic_filing(_submissions(*self.ROWS), filed_by=date(2026, 8, 4)).accession == "0000000001-26-000004"
        assert latest_periodic_filing(_submissions(*self.ROWS), filed_by=date(2026, 1, 1)) is None
        assert latest_periodic_filing(_submissions(*self.ROWS)).accession == "0000000001-26-000010"

    def test_malformed_submissions_locate_nothing(self):
        for payload in (None, [], {}, {"filings": {}}, _submissions(("x", "10-Q", "not a date", ""))):
            assert latest_periodic_filing(payload) is None

    def test_one_counted_request(self):
        calls, counted = [], []
        provider = SecEdgarShareClassProvider(lambda url, headers: calls.append(url) or {"filings": {}}, None)
        provider.fetch_submissions(cik="1108524", on_request=lambda: counted.append(1))
        assert calls == [submissions_url("1108524")] == ["https://data.sec.gov/submissions/CIK0001108524.json"]
        assert counted == [1]


def test_the_adapter_names_no_corpus_ticker():
    code = _code_without_docstrings(MODULE)
    for ticker in ("AAPL", "AMAT", "AMD", "AMZN", "CAT", "CRM", "CRWD", "DE", "GOOG", "GOOGL", "MA", "MCO", "META",
                   "MSFT", "MU", "NVDA", "TSLA", "UNP", "V", "VST"):
        assert not re.search(rf"\b{ticker}\b", code), ticker
    assert "CommonStockMember" not in code  # no member is special
