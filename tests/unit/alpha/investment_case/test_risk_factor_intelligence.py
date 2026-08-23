"""Tests for `atlas.alpha.investment_case.risk_factor_intelligence`
(Capability Expansion Sprint 17, rebuilt against this sprint's own
formal, detailed specification: `UNCLASSIFIED` fallback, the full
five-state `RiskChangeKind` history, and filing-scope-aware "no longer
disclosed" comparison).

All fake -- built entirely on `extract_filing_content` with an
injected, no-network fetcher (mirrors `test_governance_intelligence.py`
/`test_filing_content_intelligence.py`'s own convention). Live
verification against real SEC filings is done separately, outside the
unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.filing_content_intelligence import extract_filing_content
from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling
from atlas.alpha.investment_case.risk_factor_intelligence import (
    RiskCategory,
    RiskChangeKind,
    RiskDisclosureSource,
    extract_risk_factor_knowledge,
)


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


def _category(rk, kind: RiskCategory):
    return next((c for c in rk.categories if c.kind is kind), None)


def _changes_of(rk, kind: RiskChangeKind):
    return [c for c in rk.changes if c.kind is kind]


class TestEmptyInputIsHonest:
    def test_no_filings_yields_an_empty_but_real_result(self):
        rk = extract_risk_factor_knowledge(())
        assert rk.categories == ()
        assert rk.disclosures == ()
        assert rk.changes == ()
        assert rk.filings_considered == ()

    def test_a_fetch_failed_filing_contributes_nothing(self):
        content = extract_filing_content(
            _filing("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc)),
            lambda url, headers: (_ for _ in ()).throw(RuntimeError("down")),
        )
        rk = extract_risk_factor_knowledge((content,))
        assert rk.filings_considered == ()
        assert rk.disclosures == ()


class TestSectionScoping:
    def test_risk_factors_section_is_scanned(self):
        html = "<p>Item 1A. Risk Factors</p><p>We face intense competition in our industry.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        business = _category(rk, RiskCategory.BUSINESS)
        assert business is not None
        assert business.disclosures[0].source is RiskDisclosureSource.RISK_FACTORS_SECTION

    def test_mda_section_is_scanned(self):
        html = "<p>Item 7. Management's Discussion and Analysis</p><p>Litigation expenses increased this quarter.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        litigation = _category(rk, RiskCategory.LITIGATION)
        assert litigation is not None
        assert litigation.disclosures[0].source is RiskDisclosureSource.MDA_SECTION

    def test_10q_risk_updates_section_is_scanned(self):
        html = "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We remain subject to litigation risk.</p>"
        content = _content("10-Q", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        litigation = _category(rk, RiskCategory.LITIGATION)
        assert litigation is not None
        assert litigation.disclosures[0].source is RiskDisclosureSource.RISK_UPDATES_SECTION

    def test_business_section_is_never_scanned(self):
        html = "<p>Item 1. Business</p><p>We face intense competition in our industry.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        assert rk.categories == ()

    def test_unattributed_paragraphs_are_never_scanned(self):
        """The pre-heading competition text lands in Filing Content
        Intelligence's own `unattributed_paragraphs`, never in a
        confirmed Item 1A section -- it must never surface as a
        `BUSINESS` disclosure. The in-section "Ordinary text." still
        correctly surfaces as `UNCLASSIFIED` (Phase 2's own fallback)."""
        html = "<p>We face intense competition in our industry, before any heading appears.</p><p>Item 1A. Risk Factors</p><p>Ordinary text.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        assert _category(rk, RiskCategory.BUSINESS) is None
        assert all(d.text != "We face intense competition in our industry, before any heading appears." for d in rk.disclosures)

    def test_def_14a_is_never_usable_here(self):
        html = "<p>We face intense competition and litigation risk in our industry.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        assert rk.categories == ()


class TestCategoryDetection:
    _CASES = (
        ("A cybersecurity incident or data breach could harm us.", RiskCategory.CYBERSECURITY),
        ("We are subject to litigation and legal proceedings.", RiskCategory.LITIGATION),
        ("Our supply chain depends on sole source suppliers.", RiskCategory.SUPPLY_CHAIN),
        ("We have significant customer concentration among a limited number of customers.", RiskCategory.CUSTOMER_CONCENTRATION),
        ("Changes in government regulation could affect our compliance requirements.", RiskCategory.REGULATORY),
        ("Climate change and new environmental regulation could increase our costs.", RiskCategory.ENVIRONMENTAL),
        ("Geopolitical tensions and tariffs could disrupt our operations.", RiskCategory.GEOPOLITICAL),
        ("Our intellectual property and information technology systems may be at risk.", RiskCategory.TECHNOLOGY),
        ("Our indebtedness and liquidity could affect our financial condition.", RiskCategory.FINANCIAL),
        ("We face intense competition and adverse economic conditions.", RiskCategory.BUSINESS),
    )

    def test_each_category_is_detected_from_its_own_real_phrase(self):
        for text, expected_kind in self._CASES:
            html = f"<p>Item 1A. Risk Factors</p><p>{text}</p>"
            content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
            rk = extract_risk_factor_knowledge((content,))
            assert _category(rk, expected_kind) is not None, f"expected {expected_kind} from: {text!r}"

    def test_a_paragraph_can_match_multiple_categories(self):
        html = "<p>Item 1A. Risk Factors</p><p>A cybersecurity breach could expose us to litigation.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        assert _category(rk, RiskCategory.CYBERSECURITY) is not None
        assert _category(rk, RiskCategory.LITIGATION) is not None
        disclosure = rk.disclosures[0]
        assert set(disclosure.categories) == {RiskCategory.CYBERSECURITY, RiskCategory.LITIGATION}

    def test_finding_carries_full_provenance(self):
        html = "<p>Item 1A. Risk Factors</p><p>We are subject to litigation and legal proceedings.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        disclosure = _category(rk, RiskCategory.LITIGATION).disclosures[0]
        assert disclosure.accession_number == "0001-24-000001"
        assert disclosure.form_type == "10-K"
        assert disclosure.section_item_number == "1A"
        assert disclosure.table_order_index is None

    def test_findings_within_a_subsection_carry_the_subsection_heading(self):
        html = "<p>Item 1A. Risk Factors</p><h2>Cybersecurity Risks</h2><p>A cybersecurity breach could harm us.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        disclosure = _category(rk, RiskCategory.CYBERSECURITY).disclosures[0]
        assert disclosure.subsection_heading == "Cybersecurity Risks"


class TestUnclassifiedFallback:
    """Phase 2's own explicit instruction: preserve real disclosed risk
    text that matches no named category as `UNCLASSIFIED`, never drop
    it and never force it into the closest real category."""

    def test_a_risk_factors_paragraph_matching_nothing_becomes_unclassified(self):
        html = "<p>Item 1A. Risk Factors</p><p>The weather affects our operations in unpredictable ways.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        unclassified = _category(rk, RiskCategory.UNCLASSIFIED)
        assert unclassified is not None
        assert unclassified.disclosures[0].text == "The weather affects our operations in unpredictable ways."

    def test_an_mda_paragraph_matching_nothing_is_not_represented_at_all(self):
        """MD&A is a broad results discussion, not a risk section --
        only its genuinely risk-flavored sentences are pulled in;
        everything else is simply not a risk disclosure."""
        html = "<p>Item 7. Management's Discussion and Analysis</p><p>Revenue grew 12% year over year driven by strong demand.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((content,))
        assert rk.categories == ()
        assert rk.disclosures == ()

    def test_unclassified_still_counts_as_risk_section_evidence_for_comparison(self):
        earlier = _content(
            "10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc),
            "<p>Item 1A. Risk Factors</p><p>The weather affects our operations in unpredictable ways.</p>",
        )
        later = _content(
            "10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 1A. Risk Factors</p><p>The weather affects our operations in unpredictable ways.</p>",
        )
        rk = extract_risk_factor_knowledge((earlier, later))
        continues = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_CONTINUES) if c.category is RiskCategory.UNCLASSIFIED]
        assert len(continues) == 1


class TestFullChangeHistory:
    """Phase 5/6: all five states, derived from a pairwise comparison
    against the immediately preceding filing with real evidence."""

    def test_newly_disclosed(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        later = _content(
            "10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p><p>Geopolitical tensions could disrupt operations.</p>",
        )
        rk = extract_risk_factor_knowledge((earlier, later))
        newly = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_NEWLY_DISCLOSED) if c.category is RiskCategory.GEOPOLITICAL]
        assert len(newly) == 1
        assert newly[0].previous_excerpts == ()
        assert newly[0].current_excerpts == ("Geopolitical tensions could disrupt operations.",)

    def test_continues_with_identical_text(self):
        html = "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>"
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), html)
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), html)
        rk = extract_risk_factor_knowledge((earlier, later))
        continues = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_CONTINUES) if c.category is RiskCategory.BUSINESS]
        assert len(continues) == 1
        assert continues[0].previous_excerpts == continues[0].current_excerpts

    def test_wording_changed_with_different_text(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition and rising costs.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        changed = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_WORDING_CHANGED) if c.category is RiskCategory.BUSINESS]
        assert len(changed) == 1
        assert changed[0].previous_excerpts == ("We face intense competition.",)
        assert changed[0].current_excerpts == ("We face intense competition and rising costs.",)

    def test_no_longer_disclosed_between_two_10ks(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>A cybersecurity breach could harm us.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        removed = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_NO_LONGER_DISCLOSED) if c.category is RiskCategory.CYBERSECURITY]
        assert len(removed) == 1
        assert removed[0].previous_excerpts == ("A cybersecurity breach could harm us.",)
        assert removed[0].current_excerpts == ()

    def test_the_very_first_filing_never_generates_a_change(self):
        only = _content("10-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        rk = extract_risk_factor_knowledge((only,))
        assert rk.changes == ()


class TestFilingScopeAwareness:
    """Phase 7's own explicit rule: a 10-Q's Risk Factors Update
    discloses only material changes since the last 10-K -- its own
    silence on a category must never be read as `NO_LONGER_DISCLOSED`."""

    def test_10k_to_10q_absence_is_not_comparable_not_no_longer_disclosed(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>A cybersecurity breach could harm us.</p>")
        later = _content("10-Q", "0001-24-000002", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We face intense competition.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        assert not any(c.kind is RiskChangeKind.RISK_CATEGORY_NO_LONGER_DISCLOSED and c.category is RiskCategory.CYBERSECURITY for c in rk.changes)
        not_comparable = [c for c in _changes_of(rk, RiskChangeKind.RISK_DISCLOSURE_NOT_COMPARABLE) if c.category is RiskCategory.CYBERSECURITY]
        assert len(not_comparable) == 1

    def test_10q_to_10q_absence_is_also_not_comparable(self):
        """The rule is about the *later* filing's own inherently
        partial disclosure convention, not specifically what preceded
        it -- a 10-Q following another 10-Q is equally unreliable for
        a "no longer disclosed" claim."""
        earlier = _content("10-Q", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>A cybersecurity breach could harm us.</p>")
        later = _content("10-Q", "0001-24-000002", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We face intense competition.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        assert not any(c.kind is RiskChangeKind.RISK_CATEGORY_NO_LONGER_DISCLOSED for c in rk.changes)
        assert any(c.kind is RiskChangeKind.RISK_DISCLOSURE_NOT_COMPARABLE and c.category is RiskCategory.CYBERSECURITY for c in rk.changes)

    def test_10q_to_10k_absence_is_reliably_no_longer_disclosed(self):
        """The next annual 10-K is expected to comprehensively restate
        its own risk factors regardless of what a prior 10-Q said, so
        its own silence on a category IS real, comparable evidence."""
        earlier = _content("10-Q", "0001-24-000001", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>A cybersecurity breach could harm us.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        removed = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_NO_LONGER_DISCLOSED) if c.category is RiskCategory.CYBERSECURITY]
        assert len(removed) == 1

    def test_newly_disclosed_into_a_10q_is_still_reported_normally(self):
        """Scope-awareness only guards the "absence" direction --
        positive new evidence in a 10-Q is always safe to report."""
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        later = _content("10-Q", "0001-24-000002", datetime(2023, 6, 1, tzinfo=timezone.utc), "<p>PART II</p><p>Item 1A. Risk Factors Update</p><p>We face intense competition. A cybersecurity breach could harm us.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        newly = [c for c in _changes_of(rk, RiskChangeKind.RISK_CATEGORY_NEWLY_DISCLOSED) if c.category is RiskCategory.CYBERSECURITY]
        assert len(newly) == 1

    def test_mda_only_evidence_never_participates_in_pairwise_comparison(self):
        """The `changes` history is scoped to Risk Factors/Risk Updates
        evidence specifically -- an MD&A-only mention never seeds a
        comparison baseline."""
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 7. Management's Discussion and Analysis</p><p>A cybersecurity breach could harm us.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>We face intense competition.</p>")
        rk = extract_risk_factor_knowledge((earlier, later))
        assert rk.changes == ()


class TestFilingsConsidered:
    def test_filings_considered_lists_accession_numbers_chronologically(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>Text.</p>")
        later = _content("10-K", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1A. Risk Factors</p><p>Text.</p>")
        rk = extract_risk_factor_knowledge((later, earlier))
        assert rk.filings_considered == ("0001-24-000001", "0001-24-000002")

    def test_a_filing_with_no_risk_relevant_content_is_still_considered(self):
        content = _content("8-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 8.01 Other Events</p><p>Text.</p>")
        rk = extract_risk_factor_knowledge((content,))
        assert rk.filings_considered == ("0001-24-000001",)
        assert rk.categories == ()


class TestArchitectureBoundary:
    def test_module_does_not_import_html_parser(self):
        import atlas.alpha.investment_case.risk_factor_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        assert "html.parser" not in text
        assert "HTMLParser" not in text

    def test_module_does_not_import_the_decision_layer_risk_evaluators(self):
        import atlas.alpha.investment_case.risk_factor_intelligence as module
        with open(module.__file__) as f:
            lines = f.readlines()
        import_lines = [line for line in lines if line.startswith("import ") or line.startswith("from ")]
        assert not any("analysis_engine.risk" in line for line in import_lines)
