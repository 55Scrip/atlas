"""Tests for `atlas.alpha.investment_case.legal_proceedings_intelligence`
(Capability Expansion Sprint 18).

All fake -- built entirely on `extract_filing_content` with an
injected, no-network fetcher (mirrors `test_risk_factor_intelligence.py`
/`test_governance_intelligence.py`'s own convention). Live verification
against real SEC filings is done separately, outside the unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.filing_content_intelligence import extract_filing_content
from atlas.alpha.investment_case.legal_proceedings_intelligence import (
    LegalChangeKind,
    LegalDisclosureSource,
    ProceedingCategory,
    extract_legal_proceedings_knowledge,
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


def _category(lk, kind: ProceedingCategory):
    return next((c for c in lk.categories if c.kind is kind), None)


def _changes_of(lk, kind: LegalChangeKind):
    return [c for c in lk.changes if c.kind is kind]


class TestEmptyInputIsHonest:
    def test_no_filings_yields_an_empty_but_real_result(self):
        lk = extract_legal_proceedings_knowledge(())
        assert lk.categories == ()
        assert lk.disclosures == ()
        assert lk.changes == ()
        assert lk.filings_considered == ()

    def test_a_fetch_failed_filing_contributes_nothing(self):
        content = extract_filing_content(
            _filing("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc)),
            lambda url, headers: (_ for _ in ()).throw(RuntimeError("down")),
        )
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.filings_considered == ()
        assert lk.disclosures == ()


class TestSectionScoping:
    def test_10k_legal_proceedings_section_is_scanned(self):
        html = "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        litigation = _category(lk, ProceedingCategory.LITIGATION)
        assert litigation is not None
        assert litigation.disclosures[0].source is LegalDisclosureSource.LEGAL_PROCEEDINGS_SECTION

    def test_mda_section_is_scanned(self):
        html = "<p>Item 7. Management's Discussion and Analysis</p><p>Litigation expenses increased due to an ongoing lawsuit.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        litigation = _category(lk, ProceedingCategory.LITIGATION)
        assert litigation is not None
        assert litigation.disclosures[0].source is LegalDisclosureSource.MDA_SECTION

    def test_10q_risk_updates_section_is_scanned_as_the_legal_proxy(self):
        html = "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We remain a defendant in ongoing litigation.</p>"
        content = _content("10-Q", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        litigation = _category(lk, ProceedingCategory.LITIGATION)
        assert litigation is not None
        assert litigation.disclosures[0].source is LegalDisclosureSource.RISK_UPDATES_SECTION

    def test_10q_part_ii_item_1_is_never_reachable(self):
        """Confirmed, disclosed limitation (see this module's own top
        docstring): Filing Content Intelligence has no item-map entry
        for 10-Q Part II Item 1, so `find_section` never returns a
        `LEGAL_PROCEEDINGS`-kind section for a 10-Q, regardless of what
        the filing's own text says. Its own content lands in
        `unattributed_paragraphs`, which this module never scans."""
        html = "<p>PART II</p><p>Item 1. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>"
        content = _content("10-Q", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        assert content.sections == ()  # Filing Content Intelligence itself never named this section
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.categories == ()

    def test_business_section_is_never_scanned(self):
        html = "<p>Item 1. Business</p><p>We are a defendant in a lawsuit.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.categories == ()

    def test_unattributed_paragraphs_are_never_scanned(self):
        html = "<p>We are a defendant in a lawsuit, before any heading appears.</p><p>Item 3. Legal Proceedings</p><p>Ordinary text.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        assert all(d.text != "We are a defendant in a lawsuit, before any heading appears." for d in lk.disclosures)

    def test_def_14a_is_never_usable_here(self):
        html = "<p>We are a defendant in a lawsuit.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.categories == ()


class TestCategoryDetection:
    _CASES = (
        ("We are a defendant in a lawsuit alleging breach.", ProceedingCategory.LITIGATION),
        ("The company received a subpoena as part of an SEC investigation.", ProceedingCategory.REGULATORY_INVESTIGATION),
        ("We are involved in a patent infringement dispute.", ProceedingCategory.INTELLECTUAL_PROPERTY),
        ("The EPA has required us to undertake remediation at a former facility.", ProceedingCategory.ENVIRONMENTAL),
        ("We are engaged in a tax dispute with the tax authority.", ProceedingCategory.TAX),
        ("We face claims related to employment and workplace practices.", ProceedingCategory.LABOR),
        ("Regulators allege antitrust and monopolization conduct.", ProceedingCategory.ANTITRUST),
        ("A securities class action was filed against the company.", ProceedingCategory.SECURITIES),
        ("A supplier alleges breach of contract in a contractual dispute.", ProceedingCategory.CONTRACT),
    )

    def test_each_category_is_detected_from_its_own_real_phrase(self):
        for text, expected_kind in self._CASES:
            html = f"<p>Item 3. Legal Proceedings</p><p>{text}</p>"
            content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
            lk = extract_legal_proceedings_knowledge((content,))
            assert _category(lk, expected_kind) is not None, f"expected {expected_kind} from: {text!r}"

    def test_a_paragraph_can_match_multiple_categories(self):
        html = "<p>Item 3. Legal Proceedings</p><p>A securities class action alleges breach of contract.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        assert _category(lk, ProceedingCategory.SECURITIES) is not None
        assert _category(lk, ProceedingCategory.CONTRACT) is not None
        disclosure = lk.disclosures[0]
        assert set(disclosure.categories) == {ProceedingCategory.SECURITIES, ProceedingCategory.CONTRACT}

    def test_finding_carries_full_provenance(self):
        html = "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        disclosure = _category(lk, ProceedingCategory.LITIGATION).disclosures[0]
        assert disclosure.accession_number == "0001-24-000001"
        assert disclosure.form_type == "10-K"
        assert disclosure.section_item_number == "3"
        assert disclosure.table_order_index is None

    def test_findings_within_a_subsection_carry_the_subsection_heading(self):
        html = "<p>Item 3. Legal Proceedings</p><h2>Patent Matters</h2><p>We are a defendant in a patent lawsuit.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        disclosure = _category(lk, ProceedingCategory.INTELLECTUAL_PROPERTY).disclosures[0]
        assert disclosure.subsection_heading == "Patent Matters"

    def test_no_proceeding_identifier_field_is_fabricated(self):
        """This sprint's own Phase 2 names a "proceeding identifier
        where possible" -- SEC filings carry no mandated per-case ID,
        so this module never invents one; `LegalProceedingDisclosure`
        has no such field at all."""
        html = "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        disclosure = lk.disclosures[0]
        assert not hasattr(disclosure, "proceeding_identifier")
        assert not hasattr(disclosure, "identifier")


class TestUnclassifiedFallback:
    def test_a_legal_proceedings_paragraph_matching_nothing_becomes_unclassified(self):
        html = "<p>Item 3. Legal Proceedings</p><p>The company is not currently a party to any material proceedings.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        unclassified = _category(lk, ProceedingCategory.UNCLASSIFIED)
        assert unclassified is not None
        assert unclassified.disclosures[0].text == "The company is not currently a party to any material proceedings."

    def test_an_mda_paragraph_matching_nothing_is_not_represented_at_all(self):
        html = "<p>Item 7. Management's Discussion and Analysis</p><p>Revenue grew 12% year over year driven by strong demand.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.categories == ()
        assert lk.disclosures == ()

    def test_a_risk_factors_paragraph_matching_nothing_is_not_represented_at_all(self):
        """RISK_FACTORS (10-K Item 1A) is treated the same as MD&A here
        -- incidental only, never the primary legal disclosure source,
        so it gets no UNCLASSIFIED fallback either."""
        html = "<p>Item 1A. Risk Factors</p><p>Our business depends on continued innovation.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.categories == ()


class TestFullChangeHistory:
    def test_new(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>")
        later = _content(
            "10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p><p>We received a subpoena from regulators as part of an investigation.</p>",
        )
        lk = extract_legal_proceedings_knowledge((earlier, later))
        newly = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_NEW) if c.category is ProceedingCategory.REGULATORY_INVESTIGATION]
        assert len(newly) == 1
        assert newly[0].previous_excerpts == ()

    def test_continues_with_identical_text(self):
        html = "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>"
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), html)
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), html)
        lk = extract_legal_proceedings_knowledge((earlier, later))
        continues = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_CONTINUES) if c.category is ProceedingCategory.LITIGATION]
        assert len(continues) == 1
        assert continues[0].previous_excerpts == continues[0].current_excerpts

    def test_wording_changed_with_different_text(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit seeking substantial damages.</p>")
        lk = extract_legal_proceedings_knowledge((earlier, later))
        changed = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_WORDING_CHANGED) if c.category is ProceedingCategory.LITIGATION]
        assert len(changed) == 1
        assert changed[0].previous_excerpts == ("We are a defendant in a lawsuit.",)
        assert changed[0].current_excerpts == ("We are a defendant in a lawsuit seeking substantial damages.",)

    def test_no_longer_disclosed_between_two_10ks(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We received a subpoena as part of a regulatory investigation.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in an unrelated lawsuit.</p>")
        lk = extract_legal_proceedings_knowledge((earlier, later))
        removed = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_NO_LONGER_DISCLOSED) if c.category is ProceedingCategory.REGULATORY_INVESTIGATION]
        assert len(removed) == 1
        assert removed[0].current_excerpts == ()

    def test_no_longer_disclosed_never_implies_resolution_semantically(self):
        """A structural guard against future accidental over-claiming
        in this module's own vocabulary. Reads the source text directly
        -- `Enum` member docstrings are not exposed via `.__doc__` at
        the instance level (that returns the class's own docstring), so
        this checks the real, disclosed source comment instead."""
        import atlas.alpha.investment_case.legal_proceedings_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        import re as _re

        start = text.index("LEGAL_PROCEEDING_NO_LONGER_DISCLOSED = ")
        end = text.index("LEGAL_PROCEEDING_NOT_COMPARABLE = ")
        member_block = _re.sub(r"\s+", " ", text[start:end]).lower()
        for forbidden in ("dismissed", "settled", "won", "lost"):
            assert forbidden in member_block, f"{forbidden!r} should be explicitly named as forbidden"
        assert "must never be read as" in member_block

    def test_the_very_first_filing_never_generates_a_change(self):
        only = _content("10-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>")
        lk = extract_legal_proceedings_knowledge((only,))
        assert lk.changes == ()


class TestFilingScopeAwareness:
    def test_10k_to_10q_absence_is_not_comparable_not_no_longer_disclosed(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We received a subpoena as part of a regulatory investigation.</p>")
        later = _content("10-Q", "0001-24-000002", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We are a defendant in an unrelated lawsuit.</p>")
        lk = extract_legal_proceedings_knowledge((earlier, later))
        assert not any(c.kind is LegalChangeKind.LEGAL_PROCEEDING_NO_LONGER_DISCLOSED and c.category is ProceedingCategory.REGULATORY_INVESTIGATION for c in lk.changes)
        not_comparable = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_NOT_COMPARABLE) if c.category is ProceedingCategory.REGULATORY_INVESTIGATION]
        assert len(not_comparable) == 1

    def test_10q_to_10k_absence_is_reliably_no_longer_disclosed(self):
        earlier = _content("10-Q", "0001-24-000001", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We received a subpoena as part of a regulatory investigation.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in an unrelated lawsuit.</p>")
        lk = extract_legal_proceedings_knowledge((earlier, later))
        removed = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_NO_LONGER_DISCLOSED) if c.category is ProceedingCategory.REGULATORY_INVESTIGATION]
        assert len(removed) == 1

    def test_new_into_a_10q_is_still_reported_normally(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in a lawsuit.</p>")
        later = _content("10-Q", "0001-24-000002", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We are a defendant in a lawsuit. We received a subpoena as part of a regulatory investigation.</p>")
        lk = extract_legal_proceedings_knowledge((earlier, later))
        newly = [c for c in _changes_of(lk, LegalChangeKind.LEGAL_PROCEEDING_NEW) if c.category is ProceedingCategory.REGULATORY_INVESTIGATION]
        assert len(newly) == 1

    def test_mda_only_evidence_never_participates_in_pairwise_comparison(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 7. Management's Discussion and Analysis</p><p>We received a subpoena as part of a regulatory investigation.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>We are a defendant in an unrelated lawsuit.</p>")
        lk = extract_legal_proceedings_knowledge((earlier, later))
        assert lk.changes == ()


class TestFilingsConsidered:
    def test_filings_considered_lists_accession_numbers_chronologically(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>Text.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 3. Legal Proceedings</p><p>Text.</p>")
        lk = extract_legal_proceedings_knowledge((later, earlier))
        assert lk.filings_considered == ("0001-24-000001", "0001-24-000002")

    def test_a_filing_with_no_legal_relevant_content_is_still_considered(self):
        content = _content("8-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 8.01 Other Events</p><p>Text.</p>")
        lk = extract_legal_proceedings_knowledge((content,))
        assert lk.filings_considered == ("0001-24-000001",)
        assert lk.categories == ()


class TestArchitectureBoundary:
    def test_module_does_not_import_html_parser(self):
        import atlas.alpha.investment_case.legal_proceedings_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        assert "html.parser" not in text
        assert "HTMLParser" not in text

    def test_module_does_not_import_the_decision_layer_risk_evaluators(self):
        import atlas.alpha.investment_case.legal_proceedings_intelligence as module
        with open(module.__file__) as f:
            lines = f.readlines()
        import_lines = [line for line in lines if line.startswith("import ") or line.startswith("from ")]
        assert not any("analysis_engine.risk" in line for line in import_lines)
