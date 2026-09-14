"""Filing-level SEC share-class evidence (Security-Level Share-Class Evidence v1).

Real controls are trimmed copies of the annual filings' own XBRL instances
(`fixtures/share_classes/<accession>.xml`: every cover row, class share fact
and annual context the parser reads, plus decoys it must not), fetched once
from EDGAR. Synthetic instances cover what no real filing exercised; each
says so.
"""
from __future__ import annotations

import ast
import re
from datetime import date
from pathlib import Path

import pytest

from atlas.business_data_providers.errors import MalformedProviderResponse
from atlas.business_data_providers.sec_edgar_share_classes import (
    CLASS_AXIS,
    EXCHANGE_MICS,
    OUTSTANDING_SHARE_CONCEPTS,
    LinkKind,
    SecEdgarShareClassProvider,
    exchange_mic,
    filing_index_url,
    parse_share_class_filing,
    select_instance,
)

FIXTURES = Path(__file__).parent / "fixtures" / "share_classes"
MODULE = Path(__file__).resolve().parents[3] / "atlas" / "business_data_providers" / "sec_edgar_share_classes.py"


def _code_without_docstrings(path: Path) -> str:
    """Source as code: comments and docstrings removed."""
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def _filing(accession: str):
    return parse_share_class_filing((FIXTURES / f"{accession}.xml").read_text())


def _links(filing) -> dict[tuple[str, str], tuple[LinkKind, str | None, float | None]]:
    return {(f.class_member, f.period_end.isoformat()): (f.link_kind, f.cover.symbol if f.cover else None, f.shares)
            for f in filing.facts}


# -- real controls ------------------------------------------------------------------------------------------


class TestAlphabet:
    def test_class_a_and_class_c_link_to_their_own_symbols_class_b_to_neither(self):
        links = _links(_filing("0001652044-26-000018"))
        assert links[("us-gaap:CommonClassAMember", "2025-12-31")] == (
            LinkKind.PROVEN_BY_SHARED_DIMENSION, "GOOGL", 5_822_000_000.0)
        assert links[("goog:CapitalClassCMember", "2025-12-31")] == (
            LinkKind.PROVEN_BY_SHARED_DIMENSION, "GOOG", 5_429_000_000.0)
        assert links[("us-gaap:CommonClassBMember", "2025-12-31")] == (LinkKind.NO_LINK, None, 837_000_000.0)

    def test_no_issuer_total_is_ever_a_class_fact(self):
        filing = _filing("0001652044-26-000018")
        assert {f.class_member for f in filing.facts} == {
            "us-gaap:CommonClassAMember", "us-gaap:CommonClassBMember", "goog:CapitalClassCMember"}
        assert all(f.source_concept in OUTSTANDING_SHARE_CONCEPTS for f in filing.facts)

    def test_notes_rows_on_the_cover_produce_nothing(self):
        filing = _filing("0001652044-26-000018")
        assert len(filing.cover_rows) == 13  # two share classes and eleven notes
        linked = {f.cover.symbol for f in filing.facts if f.cover}
        assert linked == {"GOOG", "GOOGL"}

    def test_comparative_year_end_is_linked_by_the_same_filing(self):
        links = _links(_filing("0001652044-20-000008"))
        assert links[("goog:CapitalClassCMember", "2018-12-31")][:2] == (LinkKind.PROVEN_BY_SHARED_DIMENSION, "GOOG")

    def test_the_2022_split_is_visible_only_as_a_restatement_between_filings(self):
        before = _links(_filing("0001652044-23-000016"))[("goog:CapitalClassCMember", "2021-12-31")]
        assert before == (LinkKind.PROVEN_BY_SHARED_DIMENSION, "GOOG", 6_334_000_000.0)

    def test_pre_2019_cover_has_no_12b_row_and_links_nothing(self):
        """The FY2018 cover names "GOOG, GOOGL" in one undimensioned symbol:
        no §12(b) row, no shared member, no link -- never read as text."""
        filing = _filing("0001652044-19-000004")
        assert filing.cover_rows == ()
        assert {f.link_kind for f in filing.facts} == {LinkKind.NO_LINK}


class TestMastercardAndVisa:
    def test_mastercard_class_a_is_ma_on_nyse(self):
        filing = _filing("0001141391-26-000013")
        links = _links(filing)
        assert links[("us-gaap:CommonClassAMember", "2025-12-31")] == (
            LinkKind.PROVEN_BY_SHARED_DIMENSION, "MA", 887_000_000.0)
        assert links[("us-gaap:CommonClassBMember", "2025-12-31")][0] is LinkKind.NO_LINK
        (row,) = {f.cover for f in filing.facts if f.cover}  # one row, shared by both year-ends
        assert (row.exchange, exchange_mic(row.exchange)) == ("NYSE", "XNYS")

    def test_visa_class_a_links_and_the_b1_b2_aggregate_never_does(self):
        links = _links(_filing("0001403161-25-000089"))
        assert links[("us-gaap:CommonClassAMember", "2025-09-30")] == (
            LinkKind.PROVEN_BY_SHARED_DIMENSION, "V", 1_691_000_000.0)
        for member in ("v:CommonClassB1AndB2Member", "v:CommonClassB1Member", "v:CommonClassB2Member",
                       "us-gaap:CommonClassCMember"):
            assert links[(member, "2025-09-30")][:2] == (LinkKind.NO_LINK, None)

    def test_visa_undimensioned_cover_before_fy2022_is_ambiguous(self):
        filing = _filing("0001403161-21-000060")
        (row,) = filing.cover_rows
        assert row.class_member is None and row.symbol == "V"
        assert {f.link_kind for f in filing.facts} == {LinkKind.AMBIGUOUS}


class TestAmbiguousIssuersStayWithheld:
    """META, CRWD and SHOP list one class in one undimensioned cover row.
    Which class member it is, no shared dimension says -- never inferred
    from "Class A" in the title or from there being one listing."""

    @pytest.mark.parametrize("accession", ["0001628280-26-003942", "0001535527-26-000010", "0001594805-26-000007"])
    def test_single_undimensioned_row_links_no_class(self, accession):
        filing = _filing(accession)
        (row,) = filing.cover_rows
        assert row.class_member is None and row.symbol and row.title
        assert {f.link_kind for f in filing.facts} == {LinkKind.AMBIGUOUS}
        assert all(f.cover is None for f in filing.facts)

    def test_fb_era_filing_has_no_link_and_no_symbol_mapping(self):
        filing = _filing("0001326801-19-000009")
        assert filing.cover_rows == () and {f.link_kind for f in filing.facts} == {LinkKind.NO_LINK}


class TestEligibility:
    def test_weighted_average_and_cover_counts_are_decoys_in_the_fixtures(self):
        text = (FIXTURES / "0001652044-26-000018.xml").read_text()
        assert "WeightedAverageNumberOfSharesOutstandingBasic" in text and "EntityCommonStockSharesOutstanding" in text
        filing = parse_share_class_filing(text)
        assert {f.source_concept for f in filing.facts} == {"us-gaap:CommonStockSharesOutstanding"}
        cover_dated = [f for f in filing.facts if f.period_end > filing.document_period_end]
        assert cover_dated == []

    def test_annual_period_ends_come_from_the_filing_itself(self):
        filing = _filing("0001141391-26-000013")
        assert filing.document_period_end == date(2025, 12, 31)
        assert {date(2024, 12, 31), date(2025, 12, 31)} <= set(filing.annual_period_ends)
        assert all(f.period_end in filing.annual_period_ends for f in filing.facts)

    def test_document_identity(self):
        filing = _filing("0001403161-25-000089")
        assert (int(filing.entity_cik), filing.document_type, filing.amendment, filing.fiscal_period) == (
            1403161, "10-K", False, "FY2025")


# -- synthetic matrix ---------------------------------------------------------------------------------------


def _instance(*, rows=(), facts=(), extra_contexts="", doc_end="2025-12-31"):
    """rows: (context id, member or None, title, symbol, exchange[, no-symbol flag]);
    facts: (concept, member, instant, value, unit)."""
    contexts = [
        '<xbrli:context id="FY"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001</xbrli:identifier></xbrli:entity>'
        f'<xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>{doc_end}</xbrli:endDate></xbrli:period></xbrli:context>',
    ]
    body = [
        f'<dei:DocumentPeriodEndDate contextRef="FY">{doc_end}</dei:DocumentPeriodEndDate>',
        '<dei:DocumentType contextRef="FY">10-K</dei:DocumentType>',
        '<dei:EntityCentralIndexKey contextRef="FY">0000000001</dei:EntityCentralIndexKey>',
    ]

    def ctx(cid, member, *, instant=None):
        segment = (f'<xbrli:segment><xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">{member}'
                   '</xbrldi:explicitMember></xbrli:segment>') if member else ""
        period = (f"<xbrli:instant>{instant}</xbrli:instant>" if instant
                  else f"<xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>{doc_end}</xbrli:endDate>")
        return (f'<xbrli:context id="{cid}"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001'
                f'</xbrli:identifier>{segment}</xbrli:entity><xbrli:period>{period}</xbrli:period></xbrli:context>')

    for cid, member, title, symbol, exchange, *flag in rows:
        contexts.append(ctx(cid, member))
        body.append(f'<dei:Security12bTitle contextRef="{cid}">{title}</dei:Security12bTitle>')
        if symbol is not None:
            body.append(f'<dei:TradingSymbol contextRef="{cid}">{symbol}</dei:TradingSymbol>')
        if exchange is not None:
            body.append(f'<dei:SecurityExchangeName contextRef="{cid}">{exchange}</dei:SecurityExchangeName>')
        if flag:
            body.append(f'<dei:NoTradingSymbolFlag contextRef="{cid}">{flag[0]}</dei:NoTradingSymbolFlag>')
    for i, (concept, member, instant, value, unit) in enumerate(facts):
        contexts.append(ctx(f"f{i}", member, instant=instant))
        body.append(f'<{concept} contextRef="f{i}" unitRef="{unit}" decimals="-3">{value}</{concept}>')
    return (
        '<?xml version="1.0"?><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:us-gaap="http://fasb.org/us-gaap/2025" '
        'xmlns:dei="http://xbrl.sec.gov/dei/2025" xmlns:iso4217="http://www.xbrl.org/2003/iso4217" '
        'xmlns:abc="http://abc.example/20251231">'
        '<xbrli:unit id="shares"><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unit>'
        '<xbrli:unit id="usd"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>'
        + "".join(contexts) + extra_contexts + "".join(body) + "</xbrli:xbrl>"
    )


A, B = "us-gaap:CommonClassAMember", "abc:ClassBMember"
SHARES = "us-gaap:CommonStockSharesOutstanding"


class TestSyntheticLinking:
    def test_one_row_per_member_links_each(self):
        filing = parse_share_class_filing(_instance(
            rows=[("ra", A, "Class A", "AAA", "NASDAQ"), ("rb", B, "Class B", "BBB", "NYSE")],
            facts=[(SHARES, A, "2025-12-31", 100, "shares"), (SHARES, B, "2025-12-31", 50, "shares")]))
        assert {(f.class_member, f.cover.symbol, f.link_kind) for f in filing.facts} == {
            (A, "AAA", LinkKind.PROVEN_BY_SHARED_DIMENSION), (B, "BBB", LinkKind.PROVEN_BY_SHARED_DIMENSION)}

    def test_one_symbol_on_two_members_links_neither(self):
        filing = parse_share_class_filing(_instance(
            rows=[("ra", A, "Class A", "AAA", "NASDAQ"), ("rb", B, "Class B", "AAA", "NASDAQ")],
            facts=[(SHARES, A, "2025-12-31", 100, "shares"), (SHARES, B, "2025-12-31", 50, "shares")]))
        assert {f.link_kind for f in filing.facts} == {LinkKind.AMBIGUOUS}

    def test_a_dimensioned_row_beside_an_undimensioned_one(self):
        """Capability only: the proven member stays proven; a member with no
        row of its own is ambiguous (it could be the undimensioned security)."""
        filing = parse_share_class_filing(_instance(
            rows=[("ra", A, "Class A", "AAA", "NASDAQ"), ("r0", None, "Common", "ZZZ", "NYSE")],
            facts=[(SHARES, A, "2025-12-31", 100, "shares"), (SHARES, B, "2025-12-31", 50, "shares")]))
        kinds = {f.class_member: f.link_kind for f in filing.facts}
        assert kinds == {A: LinkKind.PROVEN_BY_SHARED_DIMENSION, B: LinkKind.AMBIGUOUS}

    def test_no_trading_symbol_flag_or_missing_exchange_is_not_a_listing(self):
        for row in [("ra", A, "Class A", "AAA", "NASDAQ", "true"), ("ra", A, "Class A", "AAA", None)]:
            filing = parse_share_class_filing(_instance(rows=[row], facts=[(SHARES, A, "2025-12-31", 100, "shares")]))
            assert filing.facts[0].link_kind is LinkKind.AMBIGUOUS

    def test_a_row_naming_two_symbols_is_not_one_symbol(self):
        filing = parse_share_class_filing(_instance(
            rows=[("ra", A, "Class A", "AAA", "NASDAQ")],
            facts=[(SHARES, A, "2025-12-31", 100, "shares")],
            extra_contexts="") .replace(
                '<dei:TradingSymbol contextRef="ra">AAA</dei:TradingSymbol>',
                '<dei:TradingSymbol contextRef="ra">AAA</dei:TradingSymbol><dei:TradingSymbol contextRef="ra">AAB</dei:TradingSymbol>'))
        assert filing.cover_rows[0].symbol is None and filing.facts[0].link_kind is LinkKind.AMBIGUOUS

    def test_disagreeing_values_for_one_member_and_date_are_a_conflict(self):
        filing = parse_share_class_filing(_instance(
            rows=[("ra", A, "Class A", "AAA", "NASDAQ")],
            facts=[(SHARES, A, "2025-12-31", 100, "shares"), (SHARES, A, "2025-12-31", 101, "shares")]))
        (fact,) = filing.facts
        assert fact.conflict and fact.shares is None and fact.link_kind is LinkKind.PROVEN_BY_SHARED_DIMENSION

    def test_ineligible_facts_are_not_class_facts(self):
        filing = parse_share_class_filing(_instance(
            rows=[("ra", A, "Class A", "AAA", "NASDAQ")],
            facts=[
                ("us-gaap:WeightedAverageNumberOfSharesOutstandingBasic", A, "2025-12-31", 99, "shares"),
                (SHARES, A, "2025-12-31", 100, "usd"),        # not a share unit
                (SHARES, A, "2025-06-30", 100, "shares"),     # not an annual period end
                (SHARES, None, "2025-12-31", 150, "shares"),  # undimensioned: an issuer total
            ]))
        assert filing.facts == ()


    def test_a_fact_with_a_further_dimension_is_not_a_class_count(self):
        """An equity-statement cell (class x equity component) is not the
        class's outstanding count."""
        extra = ('<xbrli:context id="x2"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000001'
                 '</xbrli:identifier><xbrli:segment>'
                 '<xbrldi:explicitMember dimension="us-gaap:StatementClassOfStockAxis">us-gaap:CommonClassAMember</xbrldi:explicitMember>'
                 '<xbrldi:explicitMember dimension="us-gaap:StatementEquityComponentsAxis">us-gaap:CommonStockMember</xbrldi:explicitMember>'
                 '</xbrli:segment></xbrli:entity><xbrli:period><xbrli:instant>2025-12-31</xbrli:instant></xbrli:period></xbrli:context>')
        text = _instance(rows=[("ra", A, "Class A", "AAA", "NASDAQ")], extra_contexts=extra).replace(
            "</xbrli:xbrl>", f'<{SHARES} contextRef="x2" unitRef="shares" decimals="-3">100</{SHARES}></xbrli:xbrl>')
        assert parse_share_class_filing(text).facts == ()


class TestFetching:
    def test_two_requests_index_then_inline_instance(self):
        index = {"directory": {"item": [
            {"name": "abc-20251231.htm", "size": "900"}, {"name": "abc-20251231_htm.xml", "size": "800"},
            {"name": "abc-20251231_lab.xml", "size": "5000"}, {"name": "FilingSummary.xml", "size": "9000"}]}}
        calls, counted = [], []

        def fetch_json(url, headers):
            calls.append(url)
            assert "User-Agent" in headers
            return index

        def fetch_text(url, headers):
            calls.append(url)
            return "<xbrl/>"

        provider = SecEdgarShareClassProvider(fetch_json, fetch_text)
        fetched = provider.fetch_instance(cik="0000000001", accession="0000000001-26-000001",
                                          on_request=lambda: counted.append(1))
        assert calls == [filing_index_url("0000000001", "0000000001-26-000001"),
                         "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/abc-20251231_htm.xml"]
        assert (fetched.requests, len(counted), fetched.instance_name) == (2, 2, "abc-20251231_htm.xml")

    def test_a_non_inline_filing_uses_its_largest_instance(self):
        index = {"directory": {"item": [{"name": "abc-20181231.xml", "size": "700"}, {"name": "abc-20181231_pre.xml", "size": "9000"},
                                        {"name": "other.xml", "size": "10"}]}}
        assert select_instance(index) == "abc-20181231.xml"
        with pytest.raises(MalformedProviderResponse):
            select_instance({"directory": {"item": []}})

    def test_unparseable_instance_is_an_error_not_an_empty_result(self):
        with pytest.raises(MalformedProviderResponse):
            parse_share_class_filing("<not xml")


class TestGenericity:
    def test_exchange_map_is_pinned(self):
        assert EXCHANGE_MICS == {"NASDAQ": "XNAS", "NYSE": "XNYS", "NYSEAMER": "XASE", "NYSEArca": "ARCX",
                                 "CboeBZX": "BATS"}
        assert exchange_mic("NASDAQ") == "XNAS" and exchange_mic("LSE") is None and exchange_mic(None) is None

    def test_the_adapter_names_no_issuer_symbol_or_member(self):
        code = _code_without_docstrings(MODULE)
        for name in ("GOOG", "GOOGL", "MA", "V", "META", "FB", "CRWD", "SHOP", "Alphabet", "Visa", "Mastercard"):
            assert not re.search(rf"\b{name}\b", code), name
        assert not re.search(r"Class ?[A-C]\b|Class[A-C]\w*Member", code)
        assert CLASS_AXIS == "us-gaap:StatementClassOfStockAxis"
