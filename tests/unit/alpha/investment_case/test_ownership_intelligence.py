"""Tests for `atlas.alpha.investment_case.ownership_intelligence`
(Capability Expansion Sprint 19).

All fake -- built entirely on `extract_filing_content` with an
injected, no-network fetcher (mirrors `test_legal_proceedings_
intelligence.py`/`test_governance_intelligence.py`'s own convention).
Live verification against real SEC filings is done separately, outside
the unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.filing_content_intelligence import extract_filing_content
from atlas.alpha.investment_case.ownership_intelligence import (
    OwnerCategory,
    OwnershipChangeKind,
    OwnershipDisclosureSource,
    extract_ownership_knowledge,
)
from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling


def _filing(form_type: str, accession: str, filed_at: datetime, url: str = "https://example.test/doc.htm") -> RegulatoryFiling:
    return RegulatoryFiling(
        form_type=form_type, filed_at=filed_at, accession_number=accession, filing_url=url,
        period_of_report=date(2024, 1, 1),
    )


def _fetcher(html: str):
    def fetch(url: str, headers):
        return html

    return fetch


def _content(form_type: str, accession: str, filed_at: datetime, html: str):
    return extract_filing_content(_filing(form_type, accession, filed_at), _fetcher(html))


def _category(ok, kind: OwnerCategory):
    return next((c for c in ok.categories if c.kind is kind), None)


def _changes_of(ok, kind: OwnershipChangeKind):
    return [c for c in ok.changes if c.kind is kind]


class TestEmptyInputIsHonest:
    def test_no_filings_yields_an_empty_but_real_result(self):
        ok = extract_ownership_knowledge(())
        assert ok.categories == ()
        assert ok.disclosures == ()
        assert ok.changes == ()
        assert ok.filings_considered == ()

    def test_a_fetch_failed_filing_contributes_nothing(self):
        content = extract_filing_content(
            _filing("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc)),
            lambda url, headers: (_ for _ in ()).throw(RuntimeError("down")),
        )
        ok = extract_ownership_knowledge((content,))
        assert ok.filings_considered == ()
        assert ok.disclosures == ()


class TestTableExtraction:
    _HTML = (
        "<table><thead><tr><th>Name</th><th>Title</th><th>Shares Beneficially Owned</th><th>Percent of Class</th></tr></thead>"
        "<tbody>"
        "<tr><td>Jane Smith</td><td>Chief Executive Officer</td><td>1,000,000</td><td>2.5%</td></tr>"
        "<tr><td>John Doe</td><td>Director</td><td>50,000</td><td>0.1%</td></tr>"
        "</tbody></table>"
    )

    def test_owners_are_extracted_from_a_labeled_table(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        ok = extract_ownership_knowledge((content,))
        names = {d.owner_name for d in ok.disclosures}
        assert names == {"Jane Smith", "John Doe"}

    def test_percentage_and_share_count_are_preserved_verbatim(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        ok = extract_ownership_knowledge((content,))
        jane = next(d for d in ok.disclosures if d.owner_name == "Jane Smith")
        assert jane.disclosed_percentage == "2.5%"
        assert jane.disclosed_share_count == "1,000,000"

    def test_title_column_classifies_executive_and_director(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        ok = extract_ownership_knowledge((content,))
        jane = next(d for d in ok.disclosures if d.owner_name == "Jane Smith")
        john = next(d for d in ok.disclosures if d.owner_name == "John Doe")
        assert OwnerCategory.EXECUTIVE_OFFICER in jane.categories
        assert OwnerCategory.DIRECTOR in john.categories

    def test_institutional_investor_detected_from_name_text(self):
        html = "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        owner = ok.disclosures[0]
        assert OwnerCategory.INSTITUTIONAL_INVESTOR in owner.categories

    def test_table_caption_informs_classification(self):
        html = (
            '<table><caption>Security Ownership of Directors and Executive Officers</caption>'
            "<thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Jane Smith</td><td>0.1%</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert OwnerCategory.DIRECTOR in ok.disclosures[0].categories

    def test_no_recognized_signal_yields_unknown(self):
        html = "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Jane Smith</td><td>0.1%</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures[0].categories == (OwnerCategory.UNKNOWN,)

    def test_a_row_with_no_name_is_never_an_owner(self):
        html = "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td></td><td>0.1%</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures == ()

    def test_a_table_with_no_name_column_is_never_an_ownership_table(self):
        html = "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody><tr><td>Revenue</td><td>100</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures == ()

    def test_an_empty_percent_cell_leaves_it_honestly_none(self):
        html = "<table><thead><tr><th>Name</th><th>Percent of Class</th><th>Shares</th></tr></thead><tbody><tr><td>Jane Smith</td><td></td><td>1,000</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures[0].disclosed_percentage is None
        assert ok.disclosures[0].disclosed_share_count == "1,000"

    def test_a_name_only_table_with_neither_percent_nor_shares_column_is_never_an_ownership_table(self):
        """Live-verified against a real AAPL DEF 14A: a "Name"-only
        table (e.g. a board/committee roster) is not an ownership
        disclosure at all -- this module never reads one merely because
        it happens to also have a "Name" column."""
        html = "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures == ()

    def test_bold_td_header_with_no_thead_is_still_recognized(self):
        """Live-verified against real DEF 14A tables (Governance
        Intelligence 2.0's own precedent): a header-looking row is
        routinely styled with bold `<td>` cells, not real `<th>` tags."""
        html = "<table><tr><td><b>Name</b></td><td><b>Percent of Class</b></td></tr><tr><td>Jane Smith</td><td>2.5%</td></tr></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures[0].owner_name == "Jane Smith"
        assert ok.disclosures[0].disclosed_percentage == "2.5%"

    def test_an_outstanding_equity_awards_table_is_never_read_as_an_ownership_table(self):
        """Live-verified against the real AAPL DEF 14A (accession
        0001308179-26-000008): its own "Outstanding Equity Awards at
        Fiscal Year-End" table -- an unvested-equity-award disclosure,
        not a beneficial-ownership one -- has a "Name" column and a
        "Number of Shares or Units of Stock That Have Not Vested"
        column, which `_SHARES_HEADER_RE` alone also matches, but no
        "Percent"-labeled column. Without excluding vesting-labeled
        headers from the shares-column match, a named executive's
        unvested award count (e.g. Tim Cook's real disclosed
        "85,080") was misread as `disclosed_share_count`, conflating
        an equity award with beneficial ownership -- reproduces both
        real tables from the same real filing, alongside each other,
        the same way `extract_ownership_knowledge` actually sees them."""
        html = (
            "<table><caption>Security Ownership of Directors and Executive Officers</caption>"
            "<thead><tr><th>Name of Beneficial Owner</th><th>Shares of Common Stock Beneficially Owned(1)</th>"
            "<th>Percent of Common Stock Outstanding</th></tr></thead>"
            "<tbody><tr><td>Tim Cook</td><td>3,280,295(6)</td><td>*</td></tr></tbody></table>"
            "<table><caption>Outstanding Equity Awards at Fiscal Year-End</caption>"
            "<thead><tr><th>Name</th><th>Number of Shares or Units of Stock That Have Not Vested</th></tr></thead>"
            "<tbody><tr><td>Tim Cook</td><td>85,080</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001308179-26-000008", datetime(2026, 1, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert len(ok.disclosures) == 1
        assert ok.disclosures[0].owner_name == "Tim Cook"
        assert ok.disclosures[0].disclosed_share_count == "3,280,295(6)"
        assert not any(d.disclosed_share_count == "85,080" for d in ok.disclosures)

    def test_disclosures_carry_full_table_provenance(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        ok = extract_ownership_knowledge((content,))
        jane = next(d for d in ok.disclosures if d.owner_name == "Jane Smith")
        assert jane.accession_number == "0001-24-000001"
        assert jane.form_type == "DEF 14A"
        assert jane.source is OwnershipDisclosureSource.DEF_14A_CONTENT
        assert jane.table_order_index == 0
        assert jane.paragraph_order_index is None


class TestParagraphFallback:
    def test_an_explicit_ownership_mention_becomes_a_disclosure(self):
        html = "<p>No other person is known by us to beneficially own more than 5% of our outstanding common stock.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert len(ok.disclosures) == 1
        assert ok.disclosures[0].owner_name is None
        assert ok.disclosures[0].disclosed_percentage is None

    def test_a_paragraph_with_no_ownership_signal_is_never_a_disclosure(self):
        html = "<p>The Company's headquarters are located in Cupertino, California.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures == ()

    def test_governance_section_paragraph_mention_is_captured_and_sourced(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>Our directors beneficially own shares as disclosed in our proxy statement.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert len(ok.disclosures) == 1
        assert ok.disclosures[0].source is OwnershipDisclosureSource.GOVERNANCE_SECTION

    def test_10k_business_section_is_never_scanned(self):
        html = "<p>Item 1. Business</p><p>We beneficially own several patents and beneficially own trademarks.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures == ()

    def test_10k_unattributed_content_is_never_scanned(self):
        """The DEF 14A-style broad fallback only applies to DEF 14A
        itself -- a 10-K's own unattributed content (before any
        recognized heading) is never scanned this way."""
        html = "<p>No other person is known to beneficially own more than 5% of our stock, before any heading appears.</p><p>Item 1. Business</p><p>Text.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((content,))
        assert ok.disclosures == ()


class TestOwnershipSectionForwardCompatibility:
    def test_ownership_section_is_never_actually_populated_for_a_real_def_14a(self):
        """Confirms this module's own top docstring: `FilingSectionKind.
        OWNERSHIP` exists but Filing Content Intelligence assigns
        DEF 14A no section structure at all, so this is always empty."""
        html = "<p>Some ownership-adjacent text with no heading at all.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        assert content.sections == ()


class TestOwnershipChangeHistory:
    def test_newly_disclosed(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>")
        later = _content(
            "DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr><tr><td>BlackRock Advisors LLC</td><td>6.0%</td></tr></tbody></table>",
        )
        ok = extract_ownership_knowledge((earlier, later))
        newly = _changes_of(ok, OwnershipChangeKind.OWNER_NEWLY_DISCLOSED)
        assert len(newly) == 1
        assert newly[0].owner_name == "BlackRock Advisors LLC"
        assert newly[0].previous_excerpts == ()

    def test_continues_with_identical_text(self):
        html = "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>"
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), html)
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), html)
        ok = extract_ownership_knowledge((earlier, later))
        continues = _changes_of(ok, OwnershipChangeKind.OWNER_CONTINUES)
        assert len(continues) == 1
        assert continues[0].owner_name == "Vanguard Capital Management LLC"
        assert continues[0].previous_excerpts == continues[0].current_excerpts

    def test_wording_changed_with_different_percentage(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>9.1%</td></tr></tbody></table>")
        ok = extract_ownership_knowledge((earlier, later))
        changed = _changes_of(ok, OwnershipChangeKind.OWNER_WORDING_CHANGED)
        assert len(changed) == 1
        assert changed[0].previous_excerpts == ("8.2%",)
        assert changed[0].current_excerpts == ("9.1%",)

    def test_no_longer_disclosed_between_two_def_14as(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>BlackRock Advisors LLC</td><td>6.0%</td></tr></tbody></table>")
        ok = extract_ownership_knowledge((earlier, later))
        removed = _changes_of(ok, OwnershipChangeKind.OWNER_NO_LONGER_DISCLOSED)
        assert len(removed) == 1
        assert removed[0].owner_name == "Vanguard Capital Management LLC"
        assert removed[0].current_excerpts == ()

    def test_no_longer_disclosed_never_implies_a_sale_semantically(self):
        """A structural guard against future accidental over-claiming
        in this module's own vocabulary. Reads the source text directly
        -- `Enum` member docstrings are not exposed via `.__doc__` at
        the instance level (that returns the class's own docstring), so
        this checks the real, disclosed source comment instead."""
        import atlas.alpha.investment_case.ownership_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        import re as _re

        start = text.index("OWNER_NO_LONGER_DISCLOSED = ")
        end = text.index("OWNER_DISCLOSURE_NOT_COMPARABLE = ")
        member_block = _re.sub(r"\s+", " ", text[start:end]).lower()
        for forbidden in ("shares sold", "ownership reduced", "ownership eliminated", "control lost"):
            assert forbidden in member_block, f"{forbidden!r} should be explicitly named as forbidden"
        assert "must never be read as" in member_block

    def test_the_very_first_filing_never_generates_a_change(self):
        only = _content("DEF 14A", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>")
        ok = extract_ownership_knowledge((only,))
        assert ok.changes == ()


class TestFilingScopeAwareness:
    def test_def_14a_to_10k_absence_is_not_comparable_not_no_longer_disclosed(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>")
        later = _content(
            "10-K", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc),
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p>"
            "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>BlackRock Advisors LLC</td><td>6.0%</td></tr></tbody></table>",
        )
        ok = extract_ownership_knowledge((earlier, later))
        assert not any(c.kind is OwnershipChangeKind.OWNER_NO_LONGER_DISCLOSED and c.owner_name == "Vanguard Capital Management LLC" for c in ok.changes)
        not_comparable = [c for c in _changes_of(ok, OwnershipChangeKind.OWNER_DISCLOSURE_NOT_COMPARABLE) if c.owner_name == "Vanguard Capital Management LLC"]
        assert len(not_comparable) == 1

    def test_10k_to_def_14a_absence_is_reliably_no_longer_disclosed(self):
        earlier = _content(
            "10-K", "0001-24-000001", datetime(2023, 6, 1, tzinfo=timezone.utc),
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p>"
            "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>",
        )
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>BlackRock Advisors LLC</td><td>6.0%</td></tr></tbody></table>")
        ok = extract_ownership_knowledge((earlier, later))
        removed = [c for c in _changes_of(ok, OwnershipChangeKind.OWNER_NO_LONGER_DISCLOSED) if c.owner_name == "Vanguard Capital Management LLC"]
        assert len(removed) == 1

    def test_a_filing_with_zero_table_evidence_never_participates_in_comparison(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Vanguard Capital Management LLC</td><td>8.2%</td></tr></tbody></table>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc), "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>No table here at all.</p>")
        ok = extract_ownership_knowledge((earlier, later))
        assert ok.changes == ()


class TestFilingsConsidered:
    def test_filings_considered_lists_accession_numbers_chronologically(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Text.</p>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Text.</p>")
        ok = extract_ownership_knowledge((later, earlier))
        assert ok.filings_considered == ("0001-24-000001", "0001-24-000002")


class TestArchitectureBoundary:
    def test_module_does_not_import_html_parser(self):
        import atlas.alpha.investment_case.ownership_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        assert "html.parser" not in text
        assert "HTMLParser" not in text

    def test_module_does_not_import_the_decision_layer_risk_evaluators(self):
        import atlas.alpha.investment_case.ownership_intelligence as module
        with open(module.__file__) as f:
            lines = f.readlines()
        import_lines = [line for line in lines if line.startswith("import ") or line.startswith("from ")]
        assert not any("analysis_engine.risk" in line for line in import_lines)
