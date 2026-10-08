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
from pathlib import Path

import pytest

from atlas.alpha.investment_case.filing_content_intelligence import (
    FilingParagraph,
    FilingReference,
    FilingSection,
    FilingSubsection,
    FilingTable,
    MissingFilingArtifact,
    require_filing_content,
    ExtractionStatus,
    FilingSectionKind,
    SourcePageBox,
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


class TestOneOpenSourceItemIsOneLogicalSection:
    """Real EDGAR HTML prints the current Item's own heading again at the top of
    every page. A repeated occurrence of the heading for the section already open
    is page furniture, not a second section -- one open source Item is one logical
    `FilingSection`. Keyed on the Item number (Part-qualified where the form's own
    item map is), never on the heading surface and never on the semantic kind."""

    _REPEATED = (
        "<p>Item 1. Business</p><p>First body.</p>"
        "<p>42</p><p>ITEM 1. BUSINESS</p><p>Second body.</p>"
        "<p>Item 1A. Risk Factors</p><p>Risk body.</p>"
    )

    def test_first_item_heading_opens_a_section(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._REPEATED))
        assert find_section(content, FilingSectionKind.BUSINESS) is not None

    def test_repeated_heading_for_the_open_item_opens_no_second_section(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._REPEATED))
        business = [s for s in content.sections if s.kind is FilingSectionKind.BUSINESS]
        assert len(business) == 1

    def test_content_after_a_repeated_heading_stays_in_the_open_section(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._REPEATED))
        section = find_section(content, FilingSectionKind.BUSINESS)
        assert [p.text for p in section.paragraphs] == ["First body.", "42", "Second body."]

    def test_the_section_keeps_its_first_occurrence_provenance(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._REPEATED))
        section = find_section(content, FilingSectionKind.BUSINESS)
        first_body = section.paragraphs[0].source_event_index
        assert section.source_event_index < first_body

    def test_a_different_item_heading_still_opens_a_new_section(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._REPEATED))
        risk = find_section(content, FilingSectionKind.RISK_FACTORS)
        assert [p.text for p in risk.paragraphs] == ["Risk body."]

    def test_identity_is_the_item_number_not_the_heading_surface(self):
        """Sprint 46 measured title variation for 23 of 24 observed Items, so the
        heading surface cannot carry identity."""
        html = (
            "<p>Item 7: Management's Discussion and Analysis</p><p>Body one.</p>"
            "<p>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION</p><p>Body two.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        mda = [s for s in content.sections if s.kind is FilingSectionKind.MDA]
        assert len(mda) == 1
        assert [p.text for p in mda[0].paragraphs] == ["Body one.", "Body two."]

    def test_an_unmapped_item_still_ends_the_open_section(self):
        """The repeat guard must not keep a section open across a real boundary."""
        html = "<p>Item 1. Business</p><p>Body.</p><p>Item 4. Mine Safety</p><p>After.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert [p.text for p in find_section(content, FilingSectionKind.BUSINESS).paragraphs] == ["Body."]

    def test_a_repeated_heading_before_any_section_is_still_not_a_section(self):
        html = "<p>Cover.</p><p>Item 4. Mine Safety</p><p>Unmapped body.</p><p>Item 4. Mine Safety</p><p>More.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert find_section(content, FilingSectionKind.BUSINESS) is None

    def test_prose_mentioning_an_item_mid_sentence_is_unaffected(self):
        html = (
            "<p>Item 1. Business</p><p>Body.</p>"
            "<p>We discuss this further in Item 1 of this report, which remains our "
            "principal description of the business and is incorporated by reference "
            "here for the convenience of the reader of this annual report.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        section = find_section(content, FilingSectionKind.BUSINESS)
        assert len(section.paragraphs) == 2

    def test_a_cross_reference_sentence_opens_no_section(self):
        html = "<p>See Part III, Item 10. Directors, Executive Officers and Corporate Governance.</p>"
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections == ()

    def test_ten_q_part_qualified_items_are_not_merged(self):
        """Part I Item 1 and Part II Item 1 are different source sections."""
        html = (
            "<p>PART I</p><p>Item 1. Financial Statements</p><p>Statements body.</p>"
            "<p>PART II</p><p>Item 1. Legal Proceedings</p><p>Legal body.</p>"
        )
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        statements = find_section(content, FilingSectionKind.FINANCIAL_STATEMENTS)
        assert [p.text for p in statements.paragraphs] == ["Statements body."]
        assert [p.text for p in content.unattributed_paragraphs] == ["Legal body."]

    def test_ten_q_repeated_part_and_item_is_still_one_section(self):
        html = (
            "<p>PART I</p><p>Item 1. Financial Statements</p><p>A.</p>"
            "<p>PART I</p><p>Item 1. Financial Statements</p><p>B.</p>"
        )
        content = extract_filing_content(_filing("10-Q"), _fetcher(html))
        statements = find_section(content, FilingSectionKind.FINANCIAL_STATEMENTS)
        assert [p.text for p in statements.paragraphs] == ["A.", "B."]

    def test_no_two_sections_share_an_item_number(self):
        content = extract_filing_content(_filing("10-K"), _fetcher(self._REPEATED))
        numbers = [s.item_number for s in content.sections if s.item_number is not None]
        assert len(numbers) == len(set(numbers))

    def test_many_repeats_of_the_same_heading_all_collapse(self):
        """Mastercard prints its current Item heading on every page -- 48 times for
        one Item in the held corpus -- so suppressing only the first repeat is not
        enough. The guard must hold for every subsequent occurrence."""
        html = "<p>Item 1. Business</p><p>Body 0.</p>" + "".join(
            f"<p>{n}</p><p>ITEM 1. BUSINESS</p><p>Body {n}.</p>" for n in range(1, 6)
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = [s for s in content.sections if s.kind is FilingSectionKind.BUSINESS]
        assert len(business) == 1
        assert [p.text for p in business[0].paragraphs if p.text.startswith("Body")] == [
            f"Body {n}." for n in range(6)
        ]

    def test_the_guard_is_the_open_item_not_a_document_wide_set(self):
        """The earned rule is "same as the Item currently open", deliberately narrower
        than "any Item seen anywhere". A document that genuinely returns to an earlier
        Item after a different one must open a new section rather than be swallowed."""
        html = (
            "<p>Item 1. Business</p><p>First.</p>"
            "<p>Item 1A. Risk Factors</p><p>Risk.</p>"
            "<p>Item 1. Business</p><p>Second.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        business = [s for s in content.sections if s.kind is FilingSectionKind.BUSINESS]
        assert len(business) == 2
        assert [p.text for p in business[0].paragraphs] == ["First."]
        assert [p.text for p in business[1].paragraphs] == ["Second."]


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


# ------------------------------------------------------------------ missing artifact
class TestARequiredFilingThatCannotBeReadIsNotAnEmptyFiling:
    """Sprint 26: four cached filings vanished from a temp directory and the
    corpus built on them reported 109 records instead of 162 -- no error, just
    a smaller answer. `extract_filing_content` was behaving as designed; the
    hole was that a caller could not tell "nothing to read" from "nothing
    there". `require_filing_content` is that distinction."""

    filing = RegulatoryFiling(
        form_type="10-K", filed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        accession_number="0001692819-26-000006",
        filing_url="https://www.sec.gov/Archives/edgar/data/1/000/x.htm", period_of_report=None)

    @staticmethod
    def _gone(url, headers=None):
        raise FileNotFoundError("cached body was swept away")

    def test_the_forgiving_reader_still_never_raises(self):
        content = extract_filing_content(self.filing, self._gone)
        assert content.extraction_status is ExtractionStatus.FETCH_FAILED
        assert content.sections == () and content.unattributed_paragraphs == ()

    def test_the_strict_reader_refuses_to_call_an_unreadable_filing_empty(self):
        with pytest.raises(MissingFilingArtifact) as caught:
            require_filing_content(self.filing, self._gone)
        # the message has to name the filing, or a corpus run cannot say which
        assert "0001692819-26-000006" in str(caught.value)

    def test_a_filing_that_really_has_no_paragraphs_is_returned_not_refused(self):
        # the distinction that matters: this parsed cleanly and simply says
        # nothing, which is a real answer about the source
        content = require_filing_content(self.filing, lambda u, h=None: "<html><body></body></html>")
        assert content.extraction_status is not ExtractionStatus.FETCH_FAILED
        assert content.unattributed_paragraphs == ()

    def test_a_corpus_of_filings_cannot_silently_shrink_when_one_is_missing(self):
        # the 162 -> 109 shape, in miniature: three filings, the middle one gone
        bodies = {"a": "<html><body><p>We entered into an agreement.</p></body></html>",
                  "c": "<html><body><p>We completed the acquisition.</p></body></html>"}

        def fetch(url, headers=None):
            key = url.rsplit("/", 1)[-1]
            if key not in bodies:
                raise FileNotFoundError(key)
            return bodies[key]

        filings = [
            RegulatoryFiling(form_type="10-K", filed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                             accession_number=k, filing_url=f"https://www.sec.gov/Archives/edgar/data/1/000/{k}",
                             period_of_report=None) for k in ("a", "b", "c")]
        # the old, forgiving path reports a smaller corpus and no error at all
        quiet = [extract_filing_content(f, fetch) for f in filings]
        assert sum(len(c.unattributed_paragraphs) for c in quiet) == 2
        assert all(c is not None for c in quiet)
        # the strict path stops on the hole instead of under-reporting
        with pytest.raises(MissingFilingArtifact):
            [require_filing_content(f, fetch) for f in filings]


class TestSourceEventIndex:
    """Sprint 38. The parser builds one ordered stream of block/table/anchor
    events and then files them in three separately numbered tuples, which used
    to be the point where the order BETWEEN a paragraph and a table was lost.
    `source_event_index` is that order, and nothing else: it says which event
    came first, never that two objects belong together.
    """

    _DOC = (
        "<html><body>"
        "<p>Item 2. Properties</p>"
        "<p>Our principal facilities are:</p>"
        "<table><tr><td>Site</td><td>Use</td></tr><tr><td>A</td><td>Fab</td></tr></table>"
        "<p>We also lease other space.</p>"
        "<p><a href='#note'>See note</a></p>"
        "<p>Item 3. Legal Proceedings</p>"
        "<p>None.</p>"
        "</body></html>"
    )

    def _content(self):
        return extract_filing_content(_filing("10-K"), _fetcher(self._DOC))

    def test_a_table_between_two_paragraphs_is_ordered_between_them(self):
        """The whole point of the sprint. Both objects are index 0 in their own
        tuple, so before this field there was nothing to compare."""
        section = find_section(self._content(), FilingSectionKind.PROPERTIES)
        lead_in, after = section.paragraphs[0], section.paragraphs[1]
        table = section.tables[0]
        assert lead_in.order_index == 0 and table.order_index == 0
        assert lead_in.source_event_index < table.source_event_index < after.source_event_index

    def test_the_existing_per_type_ordinal_is_untouched(self):
        section = find_section(self._content(), FilingSectionKind.PROPERTIES)
        assert [p.order_index for p in section.paragraphs] == list(range(len(section.paragraphs)))
        assert [t.order_index for t in section.tables] == [0]
        assert section.paragraphs[0].source_event_index != section.paragraphs[0].order_index

    def test_the_counter_is_document_global_so_two_sections_compare(self):
        content = self._content()
        properties = find_section(content, FilingSectionKind.PROPERTIES)
        legal = find_section(content, FilingSectionKind.LEGAL_PROCEEDINGS)
        assert properties.paragraphs[-1].source_event_index < legal.paragraphs[0].source_event_index
        assert legal.paragraphs[0].order_index == 0

    def test_a_section_carries_its_own_heading_event(self):
        """An `Item` heading becomes no paragraph. The section carries its index,
        so the heading is not simply dropped out of the ordering."""
        content = self._content()
        properties = find_section(content, FilingSectionKind.PROPERTIES)
        assert properties.source_event_index < properties.paragraphs[0].source_event_index

    def test_every_object_in_a_document_has_a_distinct_position(self):
        content = self._content()
        seen = [s.source_event_index for s in content.sections]
        seen += [p.source_event_index for s in content.sections for p in s.paragraphs]
        seen += [t.source_event_index for s in content.sections for t in s.tables]
        seen += [r.source_event_index for s in content.sections for r in s.references]
        seen += [p.source_event_index for p in content.unattributed_paragraphs]
        assert len(seen) == len(set(seen))

    def test_sorting_by_position_reproduces_the_source_order(self):
        section = find_section(self._content(), FilingSectionKind.PROPERTIES)
        items = ([(p.source_event_index, p.text) for p in section.paragraphs]
                 + [(t.source_event_index, "<table>") for t in section.tables])
        assert [text for _, text in sorted(items)] == [
            "Our principal facilities are:", "<table>", "We also lease other space.", "See note",
        ]

    def test_an_anchor_carries_a_position_too(self):
        section = find_section(self._content(), FilingSectionKind.PROPERTIES)
        assert section.references[0].source_event_index >= 0
        assert section.references[0].order_index == 0

    def test_unattributed_content_is_numbered_from_the_same_counter(self):
        """Text before the first recognised Item heading is not renumbered into a
        sequence of its own."""
        content = extract_filing_content(
            _filing("10-K"),
            _fetcher("<html><body><p>Cover page.</p><p>Item 2. Properties</p><p>A site.</p></body></html>"),
        )
        first = content.unattributed_paragraphs[0]
        section = find_section(content, FilingSectionKind.PROPERTIES)
        assert first.source_event_index < section.source_event_index < section.paragraphs[0].source_event_index

    def test_repeated_text_keeps_two_distinct_positions(self):
        content = extract_filing_content(
            _filing("10-K"),
            _fetcher("<html><body><p>Item 2. Properties</p><p>Same.</p><p>Other.</p><p>Same.</p></body></html>"),
        )
        section = find_section(content, FilingSectionKind.PROPERTIES)
        same = [p for p in section.paragraphs if p.text == "Same."]
        assert len(same) == 2
        assert same[0].source_event_index != same[1].source_event_index

    def test_parsing_the_same_bytes_twice_gives_the_same_positions(self):
        def positions(content):
            return [(s.source_event_index, [p.source_event_index for p in s.paragraphs],
                     [t.source_event_index for t in s.tables]) for s in content.sections]

        assert positions(self._content()) == positions(self._content())

    def test_table_rows_and_cells_are_not_given_positions_of_their_own(self):
        """The upstream stream emits one event per table. Giving a row or a cell
        a document position would invent an ordering the parser never had."""
        section = find_section(self._content(), FilingSectionKind.PROPERTIES)
        table = section.tables[0]
        row = table.rows[0] if table.rows else table.header.rows[0]
        assert not hasattr(row, "source_event_index")
        assert not hasattr(row.cells[0], "source_event_index")

    def test_positions_are_not_contiguous_when_an_item_heading_is_unmapped(self):
        """An `Item` heading Atlas cannot name ends the previous section and opens
        none, so it carries no position. Renumbering to close that gap would break
        correspondence with the event stream."""
        content = extract_filing_content(
            _filing("10-K"),
            _fetcher("<html><body><p>Item 2. Properties</p><p>A site.</p>"
                     "<p>Item 4. Mine Safety Disclosures</p><p>Not applicable.</p></body></html>"),
        )
        section = find_section(content, FilingSectionKind.PROPERTIES)
        carried = {s.source_event_index for s in content.sections}
        carried |= {p.source_event_index for s in content.sections for p in s.paragraphs}
        carried |= {p.source_event_index for p in content.unattributed_paragraphs}
        assert section.paragraphs[0].source_event_index + 1 not in carried

    def test_a_position_names_the_event_it_came_from(self):
        """The invariant the whole field rests on: the value is an index into the
        document's own event stream, and the event it lands on is of the object's
        own kind. A counter that merely increases would satisfy the ordering tests
        while no longer corresponding to anything in the source."""
        from atlas.alpha.investment_case.filing_content_intelligence import (
            _AnchorEvent, _BlockEvent, _parse_html, _TableEvent,
        )

        events = _parse_html(self._DOC)
        content = self._content()
        checked = 0
        for section in content.sections:
            assert isinstance(events[section.source_event_index], _BlockEvent)
            for paragraph in section.paragraphs:
                assert isinstance(events[paragraph.source_event_index], _BlockEvent)
                assert events[paragraph.source_event_index].text == paragraph.text
                checked += 1
            for table in section.tables:
                assert isinstance(events[table.source_event_index], _TableEvent)
                checked += 1
            for reference in section.references:
                assert isinstance(events[reference.source_event_index], _AnchorEvent)
                checked += 1
        assert checked >= 5

    def test_the_field_is_required_rather_than_defaulted(self):
        """A position of 'unknown' would be a lie about a parsed object, so the
        contract has no default to fall back on."""
        import dataclasses

        for kind in (FilingParagraph, FilingTable, FilingReference, FilingSection, FilingSubsection):
            field_ = next(f for f in dataclasses.fields(kind) if f.name == "source_event_index")
            assert field_.default is dataclasses.MISSING
            assert field_.default_factory is dataclasses.MISSING


class TestSourceEventIndexIsNotADecisionInput:
    """Sprint 38 keeps the new field a fact about the source document. The moment
    a semantic layer consults it, source ORDER starts being read as MEANING --
    "this paragraph precedes this table, therefore it introduces it" -- which is a
    hypothesis Sprint 37 left deliberately unfalsified (753 such adjacencies).

    Sprint 39 falsified it: over 1,387 adjudicated cases, a colon-terminated or
    explicitly deictic paragraph immediately before a table introduced it 803 times
    and never failed to, while dropping either condition cost 25% and 9% precision.
    Table Introduction is the one reader that earned the field, so it is named here
    file by file. A wildcard or a directory exemption would give the next reader the
    same access without the same argument, which is the whole point of this test.
    """

    _ROOT = Path(__file__).resolve().parents[4]
    _FIELD = "source_event_index"

    #: A closed list, never a prefix: the parser that assigns the field, and the
    #: files of each read model whose use of it has been measured and gated. Two
    #: layers qualify so far -- Table Introduction, which needs the field to order
    #: a paragraph against a table, and Table Presentation, which needs it only to
    #: say WHICH table an observation is about. Both entries were added by a sprint
    #: that first measured the claim; neither is a licence for the next reader.
    _PERMITTED = (
        "atlas/alpha/investment_case/filing_content_intelligence.py",
        "atlas/analysis_engine/table_introduction/contracts.py",
        "atlas/analysis_engine/table_introduction/reading.py",
        "atlas/analysis_engine/table_presentation/contracts.py",
        "atlas/analysis_engine/table_presentation/reading.py",
    )

    def _offenders(self, *relative_dirs):
        out = []
        for relative in relative_dirs:
            base = self._ROOT / relative
            if not base.exists():
                continue
            for path in base.rglob("*.py"):
                rel = str(path.relative_to(self._ROOT))
                if rel in self._PERMITTED:
                    continue
                if self._FIELD in path.read_text(encoding="utf-8"):
                    out.append(rel)
        return out

    def test_no_shadow_read_model_consults_it(self):
        assert self._offenders("atlas/analysis_engine") == []

    def test_no_decision_layer_consults_it(self):
        assert self._offenders("atlas/alpha/investment_case", "atlas/alpha/portfolio") == []

    def test_nothing_in_production_but_the_parser_names_it(self):
        assert self._offenders("atlas") == []

_HEADER_BOX = 'min-height:42.75pt;width:100%'
_FOOTER_BOX = 'bottom:0;position:absolute;width:100%'


def _boxes(html: str) -> list[tuple[str, str]]:
    """`(text, page-box name)` for every paragraph the parser emits."""
    content = extract_filing_content(_filing("10-K"), _fetcher(html))
    paragraphs = list(content.unattributed_paragraphs)
    for section in content.sections:
        paragraphs.extend(section.paragraphs)
        for subsection in section.subsections:
            paragraphs.extend(subsection.paragraphs)
    paragraphs.sort(key=lambda p: p.source_event_index)
    return [(p.text, p.source_page_box.name) for p in paragraphs]


class TestSourcePageBoxPosition:
    """Where the raw source placed a block -- never what the block means.

    Every assertion here is about source ancestry. Nothing in this class
    may assert that a page-box block is furniture, non-substantive, or
    excludable: the parser records position and stops there.
    """

    def test_block_outside_any_box_is_none(self):
        assert _boxes("<div><p>Ordinary body text.</p></div>") == [("Ordinary body text.", "NONE")]

    def test_block_inside_header_box(self):
        html = f'<div style="{_HEADER_BOX}"><div>Running header</div></div>'
        assert _boxes(html) == [("Running header", "HEADER_BOX")]

    def test_block_inside_footer_box(self):
        html = f'<div style="{_FOOTER_BOX}"><div>101</div></div>'
        assert _boxes(html) == [("101", "FOOTER_BOX")]

    def test_header_state_does_not_leak_to_a_later_sibling(self):
        html = f'<div style="{_HEADER_BOX}"><div>In box</div></div><div>After box</div>'
        assert _boxes(html) == [("In box", "HEADER_BOX"), ("After box", "NONE")]

    def test_footer_state_does_not_leak_to_a_later_sibling(self):
        html = f'<div style="{_FOOTER_BOX}"><div>In box</div></div><div>After box</div>'
        assert _boxes(html) == [("In box", "FOOTER_BOX"), ("After box", "NONE")]

    def test_nested_inline_elements_keep_the_box(self):
        html = f'<div style="{_HEADER_BOX}"><div><span><strong>Deep</strong></span></div></div>'
        assert _boxes(html) == [("Deep", "HEADER_BOX")]

    def test_nested_divs_inherit_the_enclosing_box(self):
        html = f'<div style="{_HEADER_BOX}"><div><div style="text-align:center">Nested</div></div></div>'
        assert _boxes(html) == [("Nested", "HEADER_BOX")]

    def test_text_before_a_box_opens_is_not_in_the_box(self):
        html = f'<div>Before</div><div style="{_HEADER_BOX}"><div>Inside</div></div>'
        assert _boxes(html) == [("Before", "NONE"), ("Inside", "HEADER_BOX")]

    def test_identical_text_inside_and_outside_differs_only_by_position(self):
        html = (
            f'<div style="{_FOOTER_BOX}"><div>See Notes to the Consolidated Financial Statements</div></div>'
            "<div>See Notes to the Consolidated Financial Statements</div>"
        )
        assert _boxes(html) == [
            ("See Notes to the Consolidated Financial Statements", "FOOTER_BOX"),
            ("See Notes to the Consolidated Financial Statements", "NONE"),
        ]

    def test_substantive_prose_inside_a_box_is_still_recorded_as_in_the_box(self):
        #: Position is recorded regardless of what the text is. The parser
        #: does not decide that long prose cannot be page-positioned.
        prose = "This sentence is long, substantive body prose that happens to sit inside the box."
        html = f'<div style="{_HEADER_BOX}"><div>{prose}</div></div>'
        assert _boxes(html) == [(prose, "HEADER_BOX")]

    def test_a_bare_number_outside_a_box_is_none(self):
        assert _boxes("<div>101</div>") == [("101", "NONE")]

    def test_centred_text_outside_a_box_is_none(self):
        assert _boxes('<div style="text-align:center">Centred</div>') == [("Centred", "NONE")]

    def test_bold_text_outside_a_box_is_none(self):
        assert _boxes('<div><span style="font-weight:700">Bold</span></div>') == [("Bold", "NONE")]

    def test_unstyled_text_inside_a_box_is_still_in_the_box(self):
        html = f'<div style="{_HEADER_BOX}"><div>Plain</div></div>'
        assert _boxes(html) == [("Plain", "HEADER_BOX")]

    def test_min_height_alone_is_not_a_header_box(self):
        assert _boxes('<div style="min-height:42.75pt"><div>x</div></div>') == [("x", "NONE")]

    def test_width_alone_is_not_a_header_box(self):
        assert _boxes('<div style="width:100%"><div>x</div></div>') == [("x", "NONE")]

    def test_position_absolute_alone_is_not_a_footer_box(self):
        assert _boxes('<div style="position:absolute"><div>x</div></div>') == [("x", "NONE")]

    def test_bottom_zero_alone_is_not_a_footer_box(self):
        assert _boxes('<div style="bottom:0"><div>x</div></div>') == [("x", "NONE")]

    def test_a_page_break_alone_creates_no_box(self):
        html = '<hr style="page-break-after:always"/><div>After the break</div>'
        assert _boxes(html) == [("After the break", "NONE")]

    def test_declaration_order_is_irrelevant(self):
        html = '<div style="width:100%;min-height:42.75pt"><div>x</div></div>'
        assert _boxes(html) == [("x", "HEADER_BOX")]

    def test_whitespace_around_declarations_is_irrelevant(self):
        html = '<div style="  min-height : 42.75pt ;  width : 100%  "><div>x</div></div>'
        assert _boxes(html) == [("x", "HEADER_BOX")]

    def test_a_trailing_semicolon_is_harmless(self):
        html = '<div style="min-height:42.75pt;width:100%;"><div>x</div></div>'
        assert _boxes(html) == [("x", "HEADER_BOX")]

    def test_a_property_whose_name_merely_ends_in_a_known_one_does_not_match(self):
        html = '<div style="not-min-height:42.75pt;my-width:100%"><div>x</div></div>'
        assert _boxes(html) == [("x", "NONE")]

    def test_a_wider_width_value_does_not_match_one_hundred_percent(self):
        #: `width:100.000%` occurs 1,324 times in the held corpus, so a
        #: prefix match here would have been a real defect.
        html = '<div style="min-height:42.75pt;width:100.000%"><div>x</div></div>'
        assert _boxes(html) == [("x", "NONE")]
        html = '<div style="min-height:42.75pt;width:1000%"><div>x</div></div>'
        assert _boxes(html) == [("x", "NONE")]

    def test_a_longer_position_value_does_not_match_absolute(self):
        html = '<div style="position:absolutely;bottom:0"><div>x</div></div>'
        assert _boxes(html) == [("x", "NONE")]

    def test_a_non_point_min_height_does_not_match(self):
        for value in ("auto", "100%", "0px", "calc(10pt + 2pt)"):
            html = f'<div style="min-height:{value};width:100%"><div>x</div></div>'
            assert _boxes(html) == [("x", "NONE")], value

    def test_a_non_zero_bottom_does_not_match(self):
        html = '<div style="bottom:4pt;position:absolute"><div>x</div></div>'
        assert _boxes(html) == [("x", "NONE")]

    def test_a_box_style_on_a_non_div_element_does_not_match(self):
        html = f'<p style="{_HEADER_BOX}">x</p>'
        assert _boxes(html) == [("x", "NONE")]

    def test_a_table_inside_a_box_does_not_corrupt_later_positions(self):
        html = (
            f'<div style="{_HEADER_BOX}"><div>Header</div>'
            "<table><tr><td>cell</td></tr></table></div><div>After</div>"
        )
        assert _boxes(html) == [("Header", "HEADER_BOX"), ("After", "NONE")]

    def test_an_anchor_inside_a_box_does_not_corrupt_later_positions(self):
        html = (
            f'<div style="{_HEADER_BOX}"><div><a href="#t">Table of Contents</a></div></div>'
            "<div>After</div>"
        )
        assert _boxes(html) == [("Table of Contents", "HEADER_BOX"), ("After", "NONE")]

    def test_consecutive_boxes_are_each_attributed_to_themselves(self):
        html = (
            f'<div style="{_HEADER_BOX}"><div>H</div></div>'
            "<div>Body</div>"
            f'<div style="{_FOOTER_BOX}"><div>F</div></div>'
        )
        assert _boxes(html) == [("H", "HEADER_BOX"), ("Body", "NONE"), ("F", "FOOTER_BOX")]

    def test_a_footer_box_nested_inside_a_header_box_reports_the_inner_box(self):
        #: The held corpus has zero such cases. This only pins that parser
        #: state stays coherent rather than leaking: the innermost opened
        #: box wins and the outer one resumes afterwards.
        html = (
            f'<div style="{_HEADER_BOX}"><div>Outer</div>'
            f'<div style="{_FOOTER_BOX}"><div>Inner</div></div>'
            "<div>Outer again</div></div>"
        )
        assert _boxes(html) == [
            ("Outer", "HEADER_BOX"),
            ("Inner", "FOOTER_BOX"),
            ("Outer again", "HEADER_BOX"),
        ]

    def test_the_position_reaches_filingparagraph_inside_a_section(self):
        html = (
            "<p>Item 1. Business</p><p>Substantive business disclosure.</p>"
            f'<div style="{_FOOTER_BOX}"><div>12</div></div>'
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        section = content.sections[0]
        assert [(p.text, p.source_page_box) for p in section.paragraphs] == [
            ("Substantive business disclosure.", SourcePageBox.NONE),
            ("12", SourcePageBox.FOOTER_BOX),
        ]

    def test_a_page_box_block_is_not_dropped_filtered_or_reordered(self):
        #: The fact has no consumer: a positioned block stays in the
        #: section, in source order, exactly as before this sprint.
        html = (
            "<p>Item 1. Business</p><p>First.</p>"
            f'<div style="{_HEADER_BOX}"><div>Running header</div></div>'
            "<p>Second.</p>"
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        section = content.sections[0]
        assert [p.text for p in section.paragraphs] == ["First.", "Running header", "Second."]
        assert [p.order_index for p in section.paragraphs] == [0, 1, 2]

    def test_heading_detection_is_unaffected_by_box_membership(self):
        html = (
            "<p>Item 1. Business</p>"
            f'<div style="{_HEADER_BOX}"><h2>Boxed heading</h2></div>'
        )
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert [s.heading_text for s in content.sections[0].subsections] == ["Boxed heading"]

    def test_any_point_valued_min_height_qualifies_not_just_one_observed_value(self):
        #: The corpus carries 18 distinct min-height values. Pinning one of
        #: them would be exactly the hardcoded numeric §25 forbids, so every
        #: point-valued form has to behave the same.
        for value in ("42.75pt", "36pt", "54pt", "63pt", "40.46pt", "9pt"):
            html = f'<div style="min-height:{value};width:100%"><div>x</div></div>'
            assert _boxes(html) == [("x", "HEADER_BOX")], value

    def test_a_bold_div_outside_a_box_is_none(self):
        #: Boldness sits on the element's own style in real filing markup as
        #: well as on inner spans; neither form may imply a page box.
        assert _boxes('<div style="font-weight:700">Bold div</div>') == [("Bold div", "NONE")]
        html = '<div style="font-weight:700;text-align:center">Bold centred div</div>'
        assert _boxes(html) == [("Bold centred div", "NONE")]

    def test_text_pending_when_a_box_opens_belongs_outside_the_box(self):
        #: Bare text followed directly by a box-opening div: the text is still
        #: accumulating when the div is seen, so it must be flushed against the
        #: ancestry that held it, not against the box about to open.
        html = f'Pending text<div style="{_HEADER_BOX}"><div>Inside</div></div>'
        assert _boxes(html) == [("Pending text", "NONE"), ("Inside", "HEADER_BOX")]
        html = f'Pending text<div style="{_FOOTER_BOX}"><div>Inside</div></div>'
        assert _boxes(html) == [("Pending text", "NONE"), ("Inside", "FOOTER_BOX")]

    def test_detection_is_independent_of_issuer_identity(self):
        #: The fixtures below carry no issuer name at all, and a block that
        #: does name a company is still NONE when it sits outside a box.
        html = f'<div style="{_HEADER_BOX}"><div>Anonymous running header</div></div>'
        assert _boxes(html) == [("Anonymous running header", "HEADER_BOX")]
        assert _boxes("<div>Example Holdings, Inc. Form 10-K</div>") == [
            ("Example Holdings, Inc. Form 10-K", "NONE")
        ]

    def test_other_attributes_on_the_box_element_are_ignored(self):
        #: Only the style declarations the predicate names may matter. Anything
        #: else on the element -- an id, a name, any generator bookkeeping --
        #: must not be able to suppress or create a box.
        html = (
            f'<div id="Example-Co-page-1" name="hdr" style="{_HEADER_BOX}">'
            "<div>Running header</div></div>"
        )
        assert _boxes(html) == [("Running header", "HEADER_BOX")]
        html = f'<div id="Example-Co-footer" style="{_FOOTER_BOX}"><div>7</div></div>'
        assert _boxes(html) == [("7", "FOOTER_BOX")]
        assert _boxes('<div id="min-height:42.75pt;width:100%"><div>x</div></div>') == [("x", "NONE")]

    def test_detection_is_independent_of_year_and_form_wording(self):
        assert _boxes("<div>2025 Form 10-K</div>") == [("2025 Form 10-K", "NONE")]
        html = f'<div style="{_HEADER_BOX}"><div>2025 Form 10-K</div></div>'
        assert _boxes(html) == [("2025 Form 10-K", "HEADER_BOX")]

    def test_the_field_creates_no_section_and_changes_no_membership(self):
        #: The field is inert: a document made only of page-box blocks still
        #: produces no section, and box blocks inside a section stay in it.
        html = f'<div style="{_HEADER_BOX}"><div>Header only</div></div>'
        content = extract_filing_content(_filing("10-K"), _fetcher(html))
        assert content.sections == ()
        assert [p.text for p in content.unattributed_paragraphs] == ["Header only"]

    def test_parsing_is_deterministic_and_leaves_no_state_behind(self):
        html = (
            f'<div style="{_HEADER_BOX}"><div>H</div></div><div>Body</div>'
        )
        assert _boxes(html) == _boxes(html) == [("H", "HEADER_BOX"), ("Body", "NONE")]
