"""Tests for `atlas.alpha.investment_case.filing_content_intelligence`
(Capability Expansion Sprint 13, Phases 2 through 7).

All fake -- no live network anywhere in this file (mirrors every
`business_data_providers` provider test's own injectable-fetcher
pattern). Live verification against a real SEC filing is done
separately, outside the unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.filing_content_intelligence import (
    ExtractionStatus,
    FilingSectionKind,
    extract_filing_content,
    find_section,
)
from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling

_FILED_AT = datetime(2024, 11, 1, tzinfo=timezone.utc)


def _filing(form_type: str, url: str = "https://example.test/doc.htm") -> RegulatoryFiling:
    return RegulatoryFiling(
        form_type=form_type, filed_at=_FILED_AT, accession_number="0001-24-000001", filing_url=url,
        period_of_report=date(2024, 9, 28),
    )


def _fetcher(html: str):
    def fetch(url: str, headers):
        return html

    return fetch


class TestFetchFailure:
    def test_fetch_exception_yields_fetch_failed_status_not_a_raise(self):
        def failing(url, headers):
            raise RuntimeError("network down")

        content = extract_filing_content(_filing("10-K"), failing)
        assert content.extraction_status is ExtractionStatus.FETCH_FAILED
        assert content.sections == ()
        assert content.accession_number == "0001-24-000001"


class TestHeadersArePassedThrough:
    def test_headers_reach_the_fetcher(self):
        """SEC's own `www.sec.gov/Archives` host returns 403 without a
        descriptive User-Agent (confirmed by a real request during this
        sprint's own live verification) -- `extract_filing_content` must
        let a caller supply one."""
        received = {}

        def capturing(url, headers):
            received["headers"] = headers
            return "<p>Item 1. Business</p><p>Text.</p>"

        extract_filing_content(_filing("10-K"), capturing, headers={"User-Agent": "Atlas test test@example.com"})
        assert received["headers"] == {"User-Agent": "Atlas test test@example.com"}

    def test_headers_default_to_none(self):
        received = {}

        def capturing(url, headers):
            received["headers"] = headers
            return "<p>Item 1. Business</p><p>Text.</p>"

        extract_filing_content(_filing("10-K"), capturing)
        assert received["headers"] is None


class TestTenKSectionDetection:
    _HTML = """
    <html><body>
    <p>Item 1. Business</p>
    <p>We design, manufacture and market products.</p>
    <p>Item 1A. Risk Factors</p>
    <p>Our business is subject to numerous risks.</p>
    <p>Item 7. Management's Discussion and Analysis</p>
    <p>Revenue increased year over year.</p>
    </body></html>
    """

    def test_three_real_item_headings_are_detected(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        assert content.extraction_status is ExtractionStatus.EXTRACTED
        kinds = [s.kind for s in content.sections]
        assert kinds == [FilingSectionKind.BUSINESS, FilingSectionKind.RISK_FACTORS, FilingSectionKind.MDA]

    def test_paragraphs_are_attributed_to_the_correct_section(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        business = find_section(content, FilingSectionKind.BUSINESS)
        assert [p.text for p in business.paragraphs] == ["We design, manufacture and market products."]
        risk = find_section(content, FilingSectionKind.RISK_FACTORS)
        assert [p.text for p in risk.paragraphs] == ["Our business is subject to numerous risks."]

    def test_item_number_is_preserved_verbatim(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        risk = find_section(content, FilingSectionKind.RISK_FACTORS)
        assert risk.item_number == "1A"

    def test_missing_section_returns_none(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        assert find_section(content, FilingSectionKind.EXHIBITS) is None

    def test_content_before_first_heading_is_unattributed(self):
        html = "<p>Some cover page text.</p><p>Item 1. Business</p><p>Real content.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert [p.text for p in content.unattributed_paragraphs] == ["Some cover page text."]

    def test_mid_sentence_item_reference_is_not_treated_as_a_heading(self):
        html = (
            "<p>Item 1. Business</p>"
            "<p>Real content here.</p>"
            "<p>As discussed in Item 1A of this report, our business faces risks related to competition, "
            "regulation, and other factors that could materially affect our results of operations over time.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert len(content.sections) == 1
        business = content.sections[0]
        assert len(business.paragraphs) == 2


class TestTenQUsesADifferentItemMapThanTenK(object):
    def test_item_1a_under_part_ii_means_risk_updates_not_risk_factors(self):
        html = "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>No material changes.</p>"
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        assert content.sections[0].kind is FilingSectionKind.RISK_UPDATES

    def test_item_1_under_part_i_means_financial_statements_not_business(self):
        html = "<p>PART I</p><p>Item 1. Financial Statements</p><p>See attached.</p>"
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        assert content.sections[0].kind is FilingSectionKind.FINANCIAL_STATEMENTS

    def test_item_2_under_part_i_means_mda(self):
        html = "<p>PART I</p><p>Item 2. Management's Discussion and Analysis</p><p>Revenue grew.</p>"
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        assert content.sections[0].kind is FilingSectionKind.MDA

    def test_item_2_under_part_ii_is_not_mislabeled_as_mda(self):
        """Part II's own real Item 2 ("Unregistered Sales of Equity
        Securities") has no member in this sprint's own 10-Q taxonomy
        -- it must resolve to unattributed, never be force-fit into
        Part I's unrelated "MD&A" meaning for the same bare number."""
        html = "<p>PART I</p><p>Item 2. MD&A</p><p>Real MD&A text.</p><p>PART II</p><p>Item 2. Unregistered Sales</p><p>None to report.</p>"
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        kinds = [s.kind for s in content.sections]
        assert kinds == [FilingSectionKind.MDA]
        assert "None to report." in [p.text for p in content.unattributed_paragraphs]

    def test_item_1_without_a_part_heading_is_not_confidently_attributed(self):
        """No `PART` heading at all means Atlas genuinely does not know
        whether a bare "Item 1" means Financial Statements (Part I) or
        Legal Proceedings (Part II) -- it must not guess."""
        html = "<p>Item 1. Something</p><p>Ambiguous content.</p>"
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        assert content.sections == ()


class TestEightKDecimalItemNumbers:
    def test_item_5_02_is_executive_change(self):
        html = "<p>Item 5.02 Departure of Directors or Certain Officers</p><p>Jane Doe resigned.</p>"
        content = extract_filing_content(_filing("8-K"), _fetcher(html))
        assert content.sections[0].kind is FilingSectionKind.EXECUTIVE_CHANGE
        assert content.sections[0].item_number == "5.02"

    def test_item_2_02_is_financial_results(self):
        html = "<p>Item 2.02 Results of Operations and Financial Condition</p><p>Revenue reported.</p>"
        content = extract_filing_content(_filing("8-K"), _fetcher(html))
        assert content.sections[0].kind is FilingSectionKind.FINANCIAL_RESULTS


class TestDef14aHasNoSectionDetection:
    def test_def_14a_always_yields_structure_unknown(self):
        html = "<p>Executive Compensation</p><p>Details about pay programs.</p>"
        content = extract_filing_content(_filing("DEF 14A"), _fetcher(html))
        assert content.extraction_status is ExtractionStatus.STRUCTURE_UNKNOWN
        assert content.sections == ()

    def test_def_14a_content_is_still_preserved_as_unattributed(self):
        html = "<p>Executive Compensation</p><p>Details about pay programs.</p>"
        content = extract_filing_content(_filing("DEF 14A"), _fetcher(html))
        assert [p.text for p in content.unattributed_paragraphs] == [
            "Executive Compensation", "Details about pay programs.",
        ]


class TestTableExtraction:
    def test_table_row_and_column_counts_are_captured(self):
        html = (
            "<p>Item 1. Business</p>"
            "<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert len(business.tables) == 1
        assert business.tables[0].row_count == 2
        assert business.tables[0].column_count == 2

    def test_table_cell_text_is_never_collected_as_paragraph_prose(self):
        html = "<p>Item 1. Business</p><table><tr><td>Confidential Cell Text</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert all("Confidential Cell Text" not in p.text for p in business.paragraphs)

    def test_nested_tables_do_not_corrupt_row_counts(self):
        html = (
            "<p>Item 1. Business</p>"
            "<table><tr><td><table><tr><td>inner</td></tr></table></td><td>outer2</td></tr></table>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert len(business.tables) == 2
        assert business.tables[0].row_count == 1 and business.tables[0].column_count == 1
        assert business.tables[1].row_count == 1 and business.tables[1].column_count == 2


class TestReferenceExtraction:
    def test_anchor_text_and_href_are_captured(self):
        html = '<p>Item 1. Business</p><p>See <a href="#note5">Note 5</a> for details.</p>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert len(business.references) == 1
        assert business.references[0].text == "Note 5"
        assert business.references[0].target == "#note5"

    def test_anchor_with_no_href_is_not_captured(self):
        html = '<p>Item 1. Business</p><p>See <a name="anchor">Note 5</a> for details.</p>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert business.references == ()


class TestScriptAndStyleAreExcluded:
    def test_script_content_never_appears_in_extracted_text(self):
        html = "<p>Item 1. Business</p><script>var secret = 'not real filing content';</script><p>Real text.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert all("secret" not in p.text for p in business.paragraphs)
        assert [p.text for p in business.paragraphs] == ["Real text."]


class TestProvenance:
    def test_filing_content_carries_real_filing_metadata(self):
        content = extract_filing_content(_filing("10-K"), _fetcher("<p>Item 1. Business</p><p>Text.</p>"))
        assert content.form_type == "10-K"
        assert content.filed_at == _FILED_AT
        assert content.accession_number == "0001-24-000001"
        assert content.source_reference == "https://example.test/doc.htm"
