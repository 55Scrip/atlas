"""Tests for `atlas.alpha.investment_case.governance_intelligence`
(Capability Expansion Sprint 15; extended by Sprint 16's own
table-aware board/committee/voting extraction).

All fake -- built entirely on `extract_filing_content` with an
injected, no-network fetcher (mirrors `test_filing_content_
intelligence.py`'s own convention). Live verification against real SEC
filings is done separately, outside the unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.filing_content_intelligence import extract_filing_content
from atlas.alpha.investment_case.governance_intelligence import (
    CommitteeKind,
    GovernanceChangeKind,
    GovernanceFindingKind,
    GovernanceObservationKind,
    extract_governance_knowledge,
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


class TestEmptyInputIsHonest:
    def test_no_filings_yields_an_empty_but_real_result(self):
        gk = extract_governance_knowledge(())
        assert gk.findings == ()
        assert gk.changes == ()
        assert gk.observations == ()
        assert gk.committees == ()
        assert gk.board_composition.chair_disclosed is False
        assert gk.board_composition.directors == ()
        assert gk.voting_structure.dual_class_disclosed is False
        assert gk.filings_considered == ()

    def test_a_fetch_failed_filing_contributes_nothing(self):
        content = extract_filing_content(_filing("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc)), lambda url, headers: (_ for _ in ()).throw(RuntimeError("down")))
        gk = extract_governance_knowledge((content,))
        assert gk.filings_considered == ()
        assert gk.findings == ()


class TestGovernanceAndCompensationSectionDetection:
    _HTML = (
        "<p>Item 10. Directors, Executive Officers and Corporate Governance</p>"
        "<p>Board oversight details.</p>"
        "<p>Item 11. Executive Compensation</p>"
        "<p>Compensation program details.</p>"
    )

    def test_governance_section_presence_is_a_real_finding(self):
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        kinds = [f.kind for f in gk.findings]
        assert GovernanceFindingKind.GOVERNANCE_SECTION_DISCLOSED in kinds
        assert GovernanceFindingKind.EXECUTIVE_COMPENSATION_DISCLOSED in kinds

    def test_finding_carries_full_provenance(self):
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        finding = next(f for f in gk.findings if f.kind is GovernanceFindingKind.GOVERNANCE_SECTION_DISCLOSED)
        assert finding.accession_number == "0001-24-000001"
        assert finding.form_type == "10-K"
        assert finding.section_item_number == "10"


class TestBoardRoleDetection:
    def test_chairman_of_the_board_sets_chair_disclosed(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>Jane Smith serves as Chairman of the Board.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.chair_disclosed is True
        assert gk.board_composition.lead_independent_director_disclosed is False
        assert len(gk.board_composition.findings) == 1
        assert gk.board_composition.findings[0].kind is GovernanceFindingKind.BOARD_CHAIR_ROLE_DISCLOSED

    def test_lead_independent_director_is_detected(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>John Doe is our Lead Independent Director.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.lead_independent_director_disclosed is True

    def test_no_role_language_leaves_flags_false(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>Nothing specific here.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.chair_disclosed is False
        assert gk.board_composition.directors == ()

    def test_directors_are_never_populated_from_paragraph_text_alone(self):
        """Sprint 16 added table-sourced director extraction, but
        paragraph prose alone (no table with a labeled `"Name"`
        column) still never yields a `Director` -- this module still
        never guesses a person's name out of free text."""
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>Jane Smith serves as Chairman of the Board. John Doe is Lead Independent Director.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors == ()


class TestCommitteeDetection:
    def test_audit_committee_is_detected(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>The Audit Committee oversees financial reporting.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert len(gk.committees) == 1
        assert gk.committees[0].kind is CommitteeKind.AUDIT
        assert gk.committees[0].disclosed_name == "Audit Committee"
        assert gk.committees[0].members == ()
        assert gk.committees[0].chair is None

    def test_multiple_distinct_committees_are_each_represented_once(self):
        html = (
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p>"
            "<p>The Audit Committee reviews filings. The Audit Committee meets quarterly. "
            "The Compensation Committee sets pay. The Risk Committee monitors exposure.</p>"
        )
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        kinds = sorted(c.kind.value for c in gk.committees)
        assert kinds == ["audit", "compensation", "risk"]

    def test_nominating_and_corporate_governance_committee_maps_to_nominating(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>The Nominating and Corporate Governance Committee selects nominees.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert [c.kind for c in gk.committees] == [CommitteeKind.NOMINATING]

    def test_no_committee_language_yields_no_committees(self):
        html = "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>General oversight text.</p>"
        content = _content("10-K", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.committees == ()


class TestVotingStructureDetection:
    def test_dual_class_language_is_detected(self):
        html = "<p>We maintain a dual-class structure with two classes of common stock.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.dual_class_disclosed is True
        assert gk.voting_structure.share_classes == ()

    def test_controlled_company_status_is_detected(self):
        html = "<p>We are a controlled company under Nasdaq listing rules.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.controlled_company_disclosed is True

    def test_no_voting_language_leaves_flags_false(self):
        html = "<p>Ordinary proxy text with no voting-structure language.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.dual_class_disclosed is False
        assert gk.voting_structure.controlled_company_disclosed is False


class TestDef14aProxyStatementFinding:
    def test_def_14a_always_yields_a_proxy_statement_finding(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), "<p>Anything at all.</p>")
        gk = extract_governance_knowledge((content,))
        kinds = [f.kind for f in gk.findings]
        assert GovernanceFindingKind.PROXY_STATEMENT_DISCLOSED in kinds

    def test_def_14a_committee_mentions_are_still_detected_from_unattributed_text(self):
        """DEF 14A gets no section structure from Filing Content
        Intelligence (Sprint 13's own decision) -- all its paragraphs
        land in `unattributed_paragraphs`, which this module still scans."""
        content = _content(
            "DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc),
            "<p>The Compensation Committee approved the new plan.</p>",
        )
        gk = extract_governance_knowledge((content,))
        assert [c.kind for c in gk.committees] == [CommitteeKind.COMPENSATION]


class TestGovernanceChangeHistory:
    def test_8k_item_5_02_becomes_a_governance_change(self):
        html = "<p>Item 5.02 Departure of Directors or Certain Officers</p><p>Jane Doe resigned as director effective March 1, 2024.</p>"
        content = _content("8-K", "0001-24-000002", datetime(2024, 4, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert len(gk.changes) == 1
        change = gk.changes[0]
        assert change.kind is GovernanceChangeKind.DIRECTOR_OR_OFFICER_CHANGE_DISCLOSED
        assert change.excerpt == "Jane Doe resigned as director effective March 1, 2024."
        assert change.accession_number == "0001-24-000002"
        assert change.section_item_number == "5.02"

    def test_8k_without_item_5_02_yields_no_change(self):
        html = "<p>Item 8.01 Other Events</p><p>Unrelated announcement.</p>"
        content = _content("8-K", "0001-24-000002", datetime(2024, 4, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.changes == ()

    def test_changes_stay_chronologically_ordered_across_multiple_8ks(self):
        earlier = _content(
            "8-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 5.02 Departure of Directors or Certain Officers</p><p>First change.</p>",
        )
        later = _content(
            "8-K", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc),
            "<p>Item 5.02 Departure of Directors or Certain Officers</p><p>Second change.</p>",
        )
        gk = extract_governance_knowledge((later, earlier))  # supplied out of order on purpose
        assert [c.excerpt for c in gk.changes] == ["First change.", "Second change."]


class TestGovernanceObservations:
    def test_a_committee_new_to_a_later_filing_is_observed(self):
        earlier = _content(
            "10-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>The Audit Committee oversees reporting.</p>",
        )
        later = _content(
            "DEF 14A", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc),
            "<p>The Compensation Committee approved new pay programs.</p>",
        )
        gk = extract_governance_knowledge((earlier, later))
        new_committee_observations = [o for o in gk.observations if o.kind is GovernanceObservationKind.NEW_COMMITTEE_DISCLOSED]
        assert len(new_committee_observations) == 1
        assert new_committee_observations[0].committee_kind is CommitteeKind.COMPENSATION
        assert new_committee_observations[0].accession_number == "0001-24-000002"

    def test_the_very_first_filing_never_generates_an_observation(self):
        """Nothing to compare against yet -- a "new" claim on the first
        filing would be unsupported, so this module never makes one."""
        only = _content(
            "10-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>The Audit Committee oversees reporting.</p>",
        )
        gk = extract_governance_knowledge((only,))
        assert gk.observations == ()

    def test_a_committee_repeated_in_a_later_filing_is_not_observed_as_new(self):
        earlier = _content(
            "10-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>The Audit Committee oversees reporting.</p>",
        )
        later = _content(
            "10-K", "0001-24-000002", datetime(2025, 1, 1, tzinfo=timezone.utc),
            "<p>Item 10. Directors, Executive Officers and Corporate Governance</p><p>The Audit Committee still oversees reporting.</p>",
        )
        gk = extract_governance_knowledge((earlier, later))
        assert gk.observations == ()

    def test_dual_class_newly_disclosed_in_a_later_filing_is_observed(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Ordinary proxy text.</p>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc), "<p>We now maintain a dual-class structure.</p>")
        gk = extract_governance_knowledge((earlier, later))
        voting_observations = [o for o in gk.observations if o.kind is GovernanceObservationKind.VOTING_STRUCTURE_DISCLOSURE_CHANGED]
        assert len(voting_observations) == 1
        assert voting_observations[0].accession_number == "0001-24-000002"

    def test_absence_of_a_previously_disclosed_flag_is_never_observed_as_a_change(self):
        """A flag can only ever newly turn True -- its disappearance in
        a later filing is never read as "this was reversed" (silence is
        not a disclosed fact)."""
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>We maintain a dual-class structure.</p>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc), "<p>Ordinary proxy text with no voting-structure language.</p>")
        gk = extract_governance_knowledge((earlier, later))
        assert gk.observations == ()
        assert gk.voting_structure.dual_class_disclosed is True


class TestFilingsConsidered:
    def test_filings_considered_lists_accession_numbers_chronologically(self):
        earlier = _content("10-K", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Item 1. Business</p><p>Text.</p>")
        later = _content("8-K", "0001-24-000002", datetime(2024, 6, 1, tzinfo=timezone.utc), "<p>Item 8.01 Other Events</p><p>Text.</p>")
        gk = extract_governance_knowledge((later, earlier))
        assert gk.filings_considered == ("0001-24-000001", "0001-24-000002")


class TestGovernancePolicyAndShareClassFramework:
    def test_policies_are_always_empty(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), "<p>Anything.</p>")
        gk = extract_governance_knowledge((content,))
        assert gk.policies == ()

    def test_share_classes_are_always_empty_even_with_dual_class_language(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), "<p>We maintain a dual-class structure.</p>")
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.share_classes == ()


class TestHeaderStyledAsBoldTdNotTh:
    """Live-verified against real AAPL DEF 14A tables: a header-looking
    row routinely uses bold `<td>` cells, not real `<th>` tags, so
    Filing Content Intelligence's own unmodified header/body split
    (correctly) does not classify it as a header. Governance
    Intelligence still recognizes it -- see `_resolve_header_and_body`."""

    def test_a_bold_td_name_row_with_no_thead_is_still_recognized_as_a_header(self):
        html = "<table><tr><td><b>Name</b></td></tr><tr><td>Jane Smith</td></tr></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert [d.name for d in gk.board_composition.directors] == ["Jane Smith"]

    def test_the_fallback_header_row_itself_never_becomes_a_director(self):
        html = "<table><tr><td>Name</td></tr><tr><td>Jane Smith</td></tr></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert [d.name for d in gk.board_composition.directors] == ["Jane Smith"]

    def test_a_table_with_no_recognizable_first_row_label_stays_unrecognized(self):
        html = "<table><tr><td>Revenue</td><td>100</td></tr></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors == ()


class TestCommitteeHeaderWordBoundaryMatching:
    """Live-verified against real AAPL DEF 14A tables: the real,
    current committee header text is "People and Compensation
    Committee," not "Compensation Committee" -- an exact-label match
    would miss it; a bounded, word-boundary substring match does not."""

    def test_a_renamed_committee_header_is_still_recognized(self):
        html = (
            "<table><thead><tr><th>Name</th><th>People and Compensation Committee</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>X</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert [c.kind for c in gk.committees] == [CommitteeKind.COMPENSATION]
        assert gk.committees[0].disclosed_name == "People and Compensation Committee"

    def test_an_unrelated_header_containing_no_committee_word_is_not_matched(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Tenure</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>8</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.committees == ()


class TestNameAndRoleInTheSameCell:
    """Live-verified against real AAPL DEF 14A tables: a filer routinely
    puts a role label in the same cell as the name, separated only by a
    `<br>` -- this module removes only the specific, already-trusted
    role phrase it matches, never guesses where a name "probably" ends."""

    def test_a_chair_phrase_embedded_in_the_name_cell_is_split_out(self):
        html = '<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Art Levinson <br/>Board Chair</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        director = gk.board_composition.directors[0]
        assert director.name == "Art Levinson"
        assert director.is_chair is True
        assert gk.board_composition.chair_disclosed is True

    def test_a_lead_independent_director_phrase_embedded_in_the_name_cell_is_split_out(self):
        html = '<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Mary Lee <br/>Lead Independent Director</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        director = gk.board_composition.directors[0]
        assert director.name == "Mary Lee"
        assert director.is_lead_independent_director is True

    def test_a_plain_name_with_no_embedded_role_is_left_untouched(self):
        html = "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors[0].name == "Jane Smith"

    def test_a_cell_that_is_only_a_role_phrase_is_never_fabricated_into_a_director(self):
        html = '<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Board Chair</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors == ()


class TestBoardTableExtraction:
    """Sprint 16, Phase 2/3: a table whose own header row literally
    labels a `"Name"` column becomes real `Director` objects."""

    _HTML = (
        "<table><thead><tr><th>Name</th><th>Position</th><th>Independent</th></tr></thead>"
        "<tbody>"
        "<tr><td>Jane Smith</td><td>Chairman of the Board</td><td>Yes</td></tr>"
        "<tr><td>John Doe</td><td></td><td>No</td></tr>"
        "</tbody></table>"
    )

    def test_directors_are_populated_from_a_labeled_name_column(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        names = [d.name for d in gk.board_composition.directors]
        assert names == ["Jane Smith", "John Doe"]

    def test_position_column_sets_chair_and_lead_independent_flags(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        jane = gk.board_composition.directors[0]
        assert jane.is_chair is True
        assert jane.is_lead_independent_director is False
        assert gk.board_composition.chair_disclosed is True

    def test_independent_column_maps_exact_yes_no_only(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        directors = {d.name: d for d in gk.board_composition.directors}
        assert directors["Jane Smith"].disclosed_independence is True
        assert directors["John Doe"].disclosed_independence is False

    def test_no_independent_column_leaves_it_honestly_none(self):
        html = "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors[0].disclosed_independence is None

    def test_ambiguous_independence_value_is_never_classified(self):
        html = '<table><thead><tr><th>Name</th><th>Independent</th></tr></thead><tbody><tr><td>Jane Smith</td><td>Partially</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors[0].disclosed_independence is None

    def test_a_row_with_no_name_is_never_a_director(self):
        html = "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td></td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors == ()

    def test_a_table_with_no_name_column_is_never_treated_as_a_board_table(self):
        html = "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody><tr><td>Revenue</td><td>100</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors == ()

    def test_a_table_with_no_header_row_at_all_is_never_treated_as_a_board_table(self):
        html = "<table><tr><td>Jane Smith</td></tr></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors == ()

    def test_tenure_column_is_read_only_as_a_plain_integer(self):
        html = '<table><thead><tr><th>Name</th><th>Tenure</th></tr></thead><tbody><tr><td>Jane Smith</td><td>8</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors[0].tenure_years == 8

    def test_director_since_style_text_never_becomes_a_computed_tenure(self):
        html = '<table><thead><tr><th>Name</th><th>Director Since</th></tr></thead><tbody><tr><td>Jane Smith</td><td>2015</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors[0].tenure_years is None

    def test_status_column_is_preserved_verbatim(self):
        html = '<table><thead><tr><th>Name</th><th>Status</th></tr></thead><tbody><tr><td>Jane Smith</td><td>Nominee</td></tr></tbody></table>'
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.board_composition.directors[0].appointment_status == "Nominee"

    def test_directors_carry_full_table_and_filing_provenance(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        director = gk.board_composition.directors[0]
        assert director.accession_number == "0001-24-000001"
        assert director.form_type == "DEF 14A"
        assert director.table_order_index == 0
        assert director.row_index == 0

    def test_board_table_disclosed_finding_is_generated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        kinds = [f.kind for f in gk.findings]
        assert GovernanceFindingKind.BOARD_TABLE_DISCLOSED in kinds


class TestCommitteeMembershipTableExtraction:
    """Sprint 16, Phase 4: per-committee mark columns inside a
    director-per-row table become real `Committee.members`/`.chair`."""

    _HTML = (
        "<table><thead><tr><th>Name</th><th>Audit</th><th>Compensation</th></tr></thead>"
        "<tbody>"
        "<tr><td>Jane Smith</td><td>Chair</td><td></td></tr>"
        "<tr><td>John Doe</td><td>X</td><td>Member</td></tr>"
        "</tbody></table>"
    )

    def test_committee_members_are_populated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        audit = next(c for c in gk.committees if c.kind is CommitteeKind.AUDIT)
        assert [m.name for m in audit.members] == ["Jane Smith", "John Doe"]

    def test_a_chair_mark_sets_the_committee_chair(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        audit = next(c for c in gk.committees if c.kind is CommitteeKind.AUDIT)
        assert audit.chair is not None
        assert audit.chair.name == "Jane Smith"

    def test_no_chair_mark_leaves_chair_honestly_none(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        compensation = next(c for c in gk.committees if c.kind is CommitteeKind.COMPENSATION)
        assert compensation.chair is None
        assert [m.name for m in compensation.members] == ["John Doe"]

    def test_a_director_has_committee_assignments_populated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        john = next(d for d in gk.board_composition.directors if d.name == "John Doe")
        assert set(john.committee_assignments) == {CommitteeKind.AUDIT, CommitteeKind.COMPENSATION}

    def test_an_empty_mark_cell_never_creates_a_membership_record(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        compensation = next(c for c in gk.committees if c.kind is CommitteeKind.COMPENSATION)
        assert "Jane Smith" not in [m.name for m in compensation.members]

    def test_disclosed_name_is_the_verbatim_header_text_not_a_synthesized_label(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        audit = next(c for c in gk.committees if c.kind is CommitteeKind.AUDIT)
        assert audit.disclosed_name == "Audit"

    def test_abbreviated_header_labels_are_recognized(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Risk</th><th>ESG</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>X</td><td>X</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        kinds = sorted(c.kind.value for c in gk.committees)
        assert kinds == ["esg", "risk"]

    def test_committee_membership_table_disclosed_finding_is_generated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        kinds = [f.kind for f in gk.findings]
        assert GovernanceFindingKind.COMMITTEE_MEMBERSHIP_TABLE_DISCLOSED in kinds

    def test_a_board_table_without_any_committee_columns_generates_no_membership_finding(self):
        html = "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        kinds = [f.kind for f in gk.findings]
        assert GovernanceFindingKind.COMMITTEE_MEMBERSHIP_TABLE_DISCLOSED not in kinds


class TestVotingStructureTableExtraction:
    """Sprint 16, Phase 5: a `"Class"`-labeled table populates real
    `ShareClass` objects."""

    _HTML = (
        "<table><thead><tr><th>Class</th><th>Votes Per Share</th></tr></thead>"
        "<tbody><tr><td>Class A</td><td>1 vote per share</td></tr>"
        "<tr><td>Class B</td><td>10 votes per share</td></tr></tbody></table>"
    )

    def test_share_classes_are_populated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        names = [sc.name for sc in gk.voting_structure.share_classes]
        assert names == ["Class A", "Class B"]

    def test_votes_per_share_is_preserved_verbatim_never_parsed(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.share_classes[0].votes_per_share == "1 vote per share"

    def test_no_votes_column_leaves_votes_per_share_empty_string(self):
        html = "<table><thead><tr><th>Class</th></tr></thead><tbody><tr><td>Class A</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.share_classes[0].votes_per_share == ""

    def test_share_classes_carry_full_provenance(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        share_class = gk.voting_structure.share_classes[0]
        assert share_class.accession_number == "0001-24-000001"
        assert share_class.table_order_index == 0
        assert share_class.row_index == 0

    def test_voting_structure_table_disclosed_finding_is_generated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        gk = extract_governance_knowledge((content,))
        kinds = [f.kind for f in gk.findings]
        assert GovernanceFindingKind.VOTING_STRUCTURE_TABLE_DISCLOSED in kinds

    def test_a_table_with_no_class_column_never_populates_share_classes(self):
        html = "<table><thead><tr><th>Metric</th></tr></thead><tbody><tr><td>Revenue</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((content,))
        assert gk.voting_structure.share_classes == ()


class TestTableSourcedMembershipObservations:
    """Sprint 16, Phase 7: comparing real, table-sourced rosters across
    filings, not just keyword mentions."""

    def _committee_table(self, name: str, mark: str = "X") -> str:
        return f"<table><thead><tr><th>Name</th><th>Audit</th></tr></thead><tbody><tr><td>{name}</td><td>{mark}</td></tr></tbody></table>"

    def test_committee_created_fires_on_second_filing_with_first_real_roster(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Nothing structured.</p>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), self._committee_table("Jane Smith"))
        gk = extract_governance_knowledge((earlier, later))
        created = [o for o in gk.observations if o.kind is GovernanceObservationKind.COMMITTEE_CREATED]
        assert len(created) == 1
        assert created[0].committee_kind is CommitteeKind.AUDIT
        assert created[0].added_names == ("Jane Smith",)

    def test_the_very_first_filing_never_generates_committee_created(self):
        only = _content("DEF 14A", "0001-24-000001", datetime(2024, 1, 1, tzinfo=timezone.utc), self._committee_table("Jane Smith"))
        gk = extract_governance_knowledge((only,))
        assert not any(o.kind is GovernanceObservationKind.COMMITTEE_CREATED for o in gk.observations)

    def test_committee_membership_changed_reports_added_and_removed_names(self):
        earlier = _content(
            "DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th><th>Audit</th></tr></thead><tbody>"
            "<tr><td>Jane Smith</td><td>X</td></tr><tr><td>John Doe</td><td>X</td></tr></tbody></table>",
        )
        later = _content(
            "DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th><th>Audit</th></tr></thead><tbody>"
            "<tr><td>Jane Smith</td><td>X</td></tr><tr><td>Mary Lee</td><td>X</td></tr></tbody></table>",
        )
        gk = extract_governance_knowledge((earlier, later))
        changed = [o for o in gk.observations if o.kind is GovernanceObservationKind.COMMITTEE_MEMBERSHIP_CHANGED]
        assert len(changed) == 1
        assert changed[0].added_names == ("Mary Lee",)
        assert changed[0].removed_names == ("John Doe",)

    def test_identical_roster_across_filings_generates_no_change_observation(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), self._committee_table("Jane Smith"))
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), self._committee_table("Jane Smith"))
        gk = extract_governance_knowledge((earlier, later))
        assert not any(o.kind is GovernanceObservationKind.COMMITTEE_MEMBERSHIP_CHANGED for o in gk.observations)

    def test_committee_removed_only_fires_when_the_later_filing_has_real_committee_evidence(self):
        earlier = _content(
            "DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th><th>Audit</th><th>Risk</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>X</td><td>X</td></tr></tbody></table>",
        )
        later = _content(
            "DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th><th>Audit</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>X</td></tr></tbody></table>",
        )
        gk = extract_governance_knowledge((earlier, later))
        removed = [o for o in gk.observations if o.kind is GovernanceObservationKind.COMMITTEE_REMOVED]
        assert len(removed) == 1
        assert removed[0].committee_kind is CommitteeKind.RISK
        assert removed[0].removed_names == ("Jane Smith",)

    def test_committee_removed_never_fires_when_the_later_filing_has_no_table_at_all(self):
        """Silence is not a disclosed fact -- a later filing with no
        committee table gives no evidence either way."""
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), self._committee_table("Jane Smith"))
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>No structured content here.</p>")
        gk = extract_governance_knowledge((earlier, later))
        assert not any(o.kind is GovernanceObservationKind.COMMITTEE_REMOVED for o in gk.observations)

    def test_board_composition_changed_reports_added_and_removed_names(self):
        earlier = _content(
            "DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr><tr><td>John Doe</td></tr></tbody></table>",
        )
        later = _content(
            "DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc),
            "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr><tr><td>Mary Lee</td></tr></tbody></table>",
        )
        gk = extract_governance_knowledge((earlier, later))
        changed = [o for o in gk.observations if o.kind is GovernanceObservationKind.BOARD_COMPOSITION_CHANGED]
        assert len(changed) == 1
        assert changed[0].added_names == ("Mary Lee",)
        assert changed[0].removed_names == ("John Doe",)

    def test_identical_board_across_filings_generates_no_change_observation(self):
        html = "<table><thead><tr><th>Name</th></tr></thead><tbody><tr><td>Jane Smith</td></tr></tbody></table>"
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), html)
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), html)
        gk = extract_governance_knowledge((earlier, later))
        assert not any(o.kind is GovernanceObservationKind.BOARD_COMPOSITION_CHANGED for o in gk.observations)


class TestArchitectureBoundary:
    """Phase 9: this module still never touches raw HTML -- it only
    reads `FilingContent`'s own already-structured fields."""

    def test_module_does_not_import_html_parser(self):
        import atlas.alpha.investment_case.governance_intelligence as module
        source = module.__file__
        with open(source) as f:
            text = f.read()
        assert "html.parser" not in text
        assert "HTMLParser" not in text
