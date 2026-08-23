"""Tests for `atlas.alpha.investment_case.filing_content_intelligence`
(Capability Expansion Sprint 13, Phases 2 through 7; extended by Sprint
14's own per-object provenance and Subsection hierarchy level; extended
by the Table Extraction infrastructure sprint's own real table
row/header/cell/caption/reference preservation).

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
    find_tables_by_keyword,
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


class TestPerObjectProvenance:
    """Sprint 14, Phase 7: every extracted object -- not just the
    top-level `FilingContent` -- carries its own accession number,
    filing date, form type, and source reference, so a `FilingSection`
    or `FilingParagraph` handed to a future capability on its own is
    still traceable back to its filing."""

    _HTML = (
        "<p>Item 1. Business</p>"
        "<p>Real content.</p>"
        '<table><tr><td>A</td></tr></table>'
        '<p>See <a href="#note5">Note 5</a> for details.</p>'
    )

    def test_section_carries_its_own_filing_provenance(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        section = content.sections[0]
        assert section.accession_number == "0001-24-000001"
        assert section.form_type == "10-K"
        assert section.filed_at == _FILED_AT
        assert section.source_reference == "https://example.test/doc.htm"
        assert section.order_index == 0

    def test_paragraph_table_and_reference_each_carry_filing_provenance(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        section = content.sections[0]
        for obj in (*section.paragraphs, *section.tables, *section.references):
            assert obj.accession_number == "0001-24-000001"
            assert obj.form_type == "10-K"
            assert obj.filed_at == _FILED_AT
            assert obj.source_reference == "https://example.test/doc.htm"

    def test_unattributed_content_also_carries_filing_provenance(self):
        html = "<p>Cover page text.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        paragraph = content.unattributed_paragraphs[0]
        assert paragraph.accession_number == "0001-24-000001"
        assert paragraph.source_reference == "https://example.test/doc.htm"

    def test_second_section_has_order_index_one(self):
        html = "<p>Item 1. Business</p><p>A.</p><p>Item 1A. Risk Factors</p><p>B.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert [s.order_index for s in content.sections] == [0, 1]


class TestSubsectionDetection:
    """Sprint 14, Phase 2: a real `<h1>`-`<h6>` heading tag inside an
    open section is a genuine, disclosed subsection boundary -- never
    inferred from text content, never fabricated when absent."""

    def test_heading_tag_inside_a_section_becomes_a_subsection(self):
        html = "<p>Item 1. Business</p><h2>Our Products</h2><p>We make things.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert len(business.subsections) == 1
        assert business.subsections[0].heading_text == "Our Products"
        assert [p.text for p in business.subsections[0].paragraphs] == ["We make things."]

    def test_content_before_first_subsection_heading_stays_on_the_section(self):
        html = "<p>Item 1. Business</p><p>Intro text.</p><h2>Our Products</h2><p>We make things.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert [p.text for p in business.paragraphs] == ["Intro text."]
        assert [p.text for p in business.subsections[0].paragraphs] == ["We make things."]

    def test_second_subsection_heading_starts_a_new_subsection(self):
        html = (
            "<p>Item 1. Business</p>"
            "<h2>Products</h2><p>Product text.</p>"
            "<h2>Services</h2><p>Services text.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        subsections = content.sections[0].subsections
        assert [s.heading_text for s in subsections] == ["Products", "Services"]
        assert [p.text for p in subsections[0].paragraphs] == ["Product text."]
        assert [p.text for p in subsections[1].paragraphs] == ["Services text."]

    def test_a_new_item_heading_ends_the_open_subsection(self):
        html = (
            "<p>Item 1. Business</p><h2>Products</h2><p>Product text.</p>"
            "<p>Item 1A. Risk Factors</p><p>Risk text.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        risk = find_section(content, FilingSectionKind.RISK_FACTORS)
        assert risk.subsections == ()
        assert [p.text for p in risk.paragraphs] == ["Risk text."]

    def test_heading_tag_outside_any_section_is_unattributed_not_a_floating_subsection(self):
        html = "<h2>Cover Page Heading</h2><p>Item 1. Business</p><p>Real content.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert [p.text for p in content.unattributed_paragraphs] == ["Cover Page Heading"]

    def test_subsection_carries_filing_provenance_and_order_index(self):
        html = "<p>Item 1. Business</p><h2>Products</h2><p>Text.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        subsection = content.sections[0].subsections[0]
        assert subsection.order_index == 0
        assert subsection.accession_number == "0001-24-000001"
        assert subsection.source_reference == "https://example.test/doc.htm"

    def test_no_heading_tags_means_no_subsections_most_real_filings_today(self):
        """Confirms Sprint 13's own real-filing-formatting finding still
        holds: a section built entirely from `<p>` text (as most real
        EDGAR filings are) has zero subsections, honestly -- not an
        error, not a guess."""
        content = extract_filing_content(_filing("10-K"), _fetcher(self.__class__._HTML_NO_HEADINGS))
        assert content.sections[0].subsections == ()

    _HTML_NO_HEADINGS = "<p>Item 1. Business</p><p>All plain paragraph text, no heading tags.</p>"


class TestTableCellTextExtraction:
    """Table Extraction sprint: real cell text is now preserved, not
    just structural counts."""

    def test_cell_text_is_preserved_verbatim(self):
        html = "<p>Item 1. Business</p><table><tr><td>Revenue</td><td>$1,000,000</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert [c.text for c in table.rows[0].cells] == ["Revenue", "$1,000,000"]

    def test_empty_cell_is_preserved_as_empty_string_not_omitted(self):
        html = "<p>Item 1. Business</p><table><tr><td>Name</td><td></td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert len(table.rows[0].cells) == 2
        assert table.rows[0].cells[1].text == ""

    def test_cell_text_is_still_never_collected_as_paragraph_prose(self):
        html = "<p>Item 1. Business</p><table><tr><td>Confidential Cell Text</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = content.sections[0]
        assert all("Confidential Cell Text" not in p.text for p in business.paragraphs)
        assert business.tables[0].rows[0].cells[0].text == "Confidential Cell Text"

    def test_row_count_and_column_count_stay_literal_and_unchanged(self):
        """Backward compatibility: row_count/column_count are never
        colspan-expanded -- unchanged in meaning from before this sprint."""
        html = "<p>Item 1. Business</p><table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert table.row_count == 2
        assert table.column_count == 2


class TestTableHeaderDetection:
    def test_thead_rows_become_the_table_header(self):
        html = (
            "<p>Item 1. Business</p>"
            "<table><thead><tr><th>Name</th><th>Value</th></tr></thead>"
            "<tbody><tr><td>Revenue</td><td>100</td></tr></tbody></table>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert table.header is not None
        assert [c.text for c in table.header.rows[0].cells] == ["Name", "Value"]
        assert table.header.rows[0].is_header_row is True
        assert len(table.rows) == 1
        assert table.rows[0].cells[0].text == "Revenue"

    def test_implicit_all_th_row_with_no_thead_is_still_a_header(self):
        html = "<p>Item 1. Business</p><table><tr><th>Name</th><th>Value</th></tr><tr><td>Revenue</td><td>100</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert table.header is not None
        assert [c.text for c in table.header.rows[0].cells] == ["Name", "Value"]
        assert len(table.rows) == 1

    def test_a_tbody_row_using_th_for_a_row_label_is_not_reclassified_as_header(self):
        """An explicit `<tbody>` group tag is a real, disclosed fact
        that always wins over the "all th" fallback -- a row-label
        `<th>` inside a real body row stays a body row."""
        html = "<p>Item 1. Business</p><table><tbody><tr><th>Revenue</th><td>100</td></tr></tbody></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert table.header is None
        assert len(table.rows) == 1
        assert table.rows[0].cells[0].is_header is True
        assert table.rows[0].is_header_row is False

    def test_no_header_row_at_all_is_honestly_none(self):
        html = "<p>Item 1. Business</p><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].header is None

    def test_th_cells_are_flagged_is_header_regardless_of_row_classification(self):
        html = "<p>Item 1. Business</p><table><thead><tr><th>Name</th></tr></thead></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        cell = content.sections[0].tables[0].header.rows[0].cells[0]
        assert cell.is_header is True


class TestTableFooter:
    def test_tfoot_rows_are_preserved_separately(self):
        html = (
            "<p>Item 1. Business</p>"
            "<table><tbody><tr><td>Revenue</td><td>100</td></tr></tbody>"
            "<tfoot><tr><td>Total</td><td>100</td></tr></tfoot></table>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert len(table.rows) == 1
        assert len(table.footer_rows) == 1
        assert table.footer_rows[0].cells[0].text == "Total"

    def test_no_tfoot_yields_an_empty_footer(self):
        html = "<p>Item 1. Business</p><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].footer_rows == ()


class TestCellSpanAndAlignmentMetadata:
    def test_rowspan_and_colspan_are_preserved(self):
        html = '<p>Item 1. Business</p><table><tr><td rowspan="2" colspan="3">X</td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        cell = content.sections[0].tables[0].rows[0].cells[0]
        assert cell.rowspan == 2
        assert cell.colspan == 3

    def test_missing_span_attributes_default_to_one_not_inferred(self):
        html = "<p>Item 1. Business</p><table><tr><td>X</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        cell = content.sections[0].tables[0].rows[0].cells[0]
        assert cell.rowspan == 1
        assert cell.colspan == 1

    def test_unparseable_span_value_falls_back_to_one(self):
        html = '<p>Item 1. Business</p><table><tr><td colspan="not-a-number">X</td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        cell = content.sections[0].tables[0].rows[0].cells[0]
        assert cell.colspan == 1

    def test_a_spanning_cell_is_never_expanded_into_synthetic_adjacent_cells(self):
        html = '<p>Item 1. Business</p><table><tr><td colspan="3">X</td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        row = content.sections[0].tables[0].rows[0]
        assert len(row.cells) == 1

    def test_align_attribute_is_preserved(self):
        html = '<p>Item 1. Business</p><table><tr><td align="right">100</td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].rows[0].cells[0].alignment == "right"

    def test_style_text_align_is_preserved(self):
        html = '<p>Item 1. Business</p><table><tr><td style="font-weight:bold;text-align:center">100</td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].rows[0].cells[0].alignment == "center"

    def test_no_alignment_information_is_honestly_none(self):
        html = "<p>Item 1. Business</p><table><tr><td>100</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].rows[0].cells[0].alignment is None


class TestTableCaptionAndHeadingContext:
    def test_caption_is_preserved_verbatim(self):
        html = "<p>Item 1. Business</p><table><caption>Table 1: Segment Revenue</caption><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].caption == "Table 1: Segment Revenue"

    def test_no_caption_is_honestly_none(self):
        html = "<p>Item 1. Business</p><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].caption is None

    def test_heading_context_reflects_the_enclosing_subsection(self):
        html = "<p>Item 1. Business</p><h2>Segment Detail</h2><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].subsections[0].tables[0]
        assert table.heading_context == "Segment Detail"

    def test_heading_context_is_none_with_no_enclosing_subsection(self):
        html = "<p>Item 1. Business</p><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].heading_context is None


class TestCellReferences:
    def test_a_link_inside_a_cell_becomes_a_cell_reference(self):
        html = '<p>Item 1. Business</p><table><tr><td>See <a href="#note5">Note 5</a> for detail.</td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        cell = content.sections[0].tables[0].rows[0].cells[0]
        assert cell.text == "See Note 5 for detail."
        assert len(cell.references) == 1
        assert cell.references[0].text == "Note 5"
        assert cell.references[0].target == "#note5"

    def test_a_link_inside_a_cell_never_leaks_into_the_prose_reference_stream(self):
        html = '<p>Item 1. Business</p><table><tr><td><a href="#note5">Note 5</a></td></tr></table>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].references == ()
        assert content.unattributed_references == ()

    def test_no_link_yields_no_cell_references(self):
        html = "<p>Item 1. Business</p><table><tr><td>Plain text</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections[0].tables[0].rows[0].cells[0].references == ()


class TestNestedTablesAfterTableExtraction:
    """Sprint 13's own nested-table handling, re-verified after the
    Table Extraction rewrite -- must still produce two separate,
    sibling `FilingTable`s with unchanged counts, now also with real
    cell text and an honest `contains_nested_table` marker."""

    _HTML = (
        "<p>Item 1. Business</p>"
        "<table><tr><td><table><tr><td>inner</td></tr></table></td><td>outer2</td></tr></table>"
    )

    def test_two_separate_tables_with_unchanged_counts(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        business = content.sections[0]
        assert len(business.tables) == 2
        assert business.tables[0].row_count == 1 and business.tables[0].column_count == 1
        assert business.tables[1].row_count == 1 and business.tables[1].column_count == 2

    def test_inner_table_cell_text_is_preserved(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        inner = content.sections[0].tables[0]
        assert inner.rows[0].cells[0].text == "inner"

    def test_outer_cell_containing_the_nested_table_is_flagged_and_has_no_leaked_text(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._HTML))
        outer = content.sections[0].tables[1]
        assert outer.rows[0].cells[0].contains_nested_table is True
        assert outer.rows[0].cells[0].text == ""
        assert outer.rows[0].cells[1].text == "outer2"
        assert outer.rows[0].cells[1].contains_nested_table is False


class TestTableObjectProvenance:
    def test_row_and_cell_carry_full_filing_provenance(self):
        html = "<p>Item 1. Business</p><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        row = table.rows[0]
        cell = row.cells[0]
        for obj in (row, cell):
            assert obj.accession_number == "0001-24-000001"
            assert obj.form_type == "10-K"
            assert obj.filed_at == _FILED_AT
            assert obj.source_reference == "https://example.test/doc.htm"

    def test_cell_carries_its_own_table_and_row_index(self):
        html = "<p>Item 1. Business</p><table><tr><td>A</td></tr><tr><td>B</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        table = content.sections[0].tables[0]
        assert table.rows[0].cells[0].row_index == 0
        assert table.rows[1].cells[0].row_index == 1
        assert table.rows[0].cells[0].table_order_index == 0
        assert table.rows[0].table_order_index == 0


class TestFindTablesByKeyword:
    def test_finds_a_table_by_its_own_caption(self):
        html = "<p>Item 1. Business</p><table><caption>Executive Compensation Summary</caption><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        found = find_tables_by_keyword(content, "compensation")
        assert len(found) == 1
        assert found[0].caption == "Executive Compensation Summary"

    def test_finds_a_table_by_its_own_heading_context(self):
        html = "<p>Item 1. Business</p><h2>Director Compensation</h2><table><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        found = find_tables_by_keyword(content, "director")
        assert len(found) == 1

    def test_match_is_case_insensitive(self):
        html = "<p>Item 1. Business</p><table><caption>OWNERSHIP TABLE</caption><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert len(find_tables_by_keyword(content, "ownership")) == 1

    def test_no_match_returns_empty(self):
        html = "<p>Item 1. Business</p><table><caption>Revenue by Segment</caption><tr><td>A</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert find_tables_by_keyword(content, "compensation") == ()

    def test_a_table_with_neither_caption_nor_heading_context_is_never_matched(self):
        html = "<p>Item 1. Business</p><table><tr><td>compensation</td></tr></table>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert find_tables_by_keyword(content, "compensation") == ()

    def test_searches_across_sections_subsections_and_unattributed_tables(self):
        html = (
            "<table><caption>Cover Compensation Table</caption><tr><td>A</td></tr></table>"
            "<p>Item 1. Business</p>"
            "<h2>Compensation Detail</h2>"
            "<table><tr><td>B</td></tr></table>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        found = find_tables_by_keyword(content, "compensation")
        assert len(found) == 2
