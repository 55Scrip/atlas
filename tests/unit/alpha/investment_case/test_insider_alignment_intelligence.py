"""Tests for `atlas.alpha.investment_case.insider_alignment_intelligence`
(Capability Expansion Sprint 21).

All fake -- built entirely on `extract_filing_content` with an
injected, no-network fetcher, then fed through the real `extract_
ownership_knowledge`/`extract_executive_compensation_knowledge` (both
unmodified) into the new module under test. Mirrors `test_executive_
compensation_intelligence.py`'s own convention. Live verification
against real SEC filings is done separately, outside the unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveIdentity, ExecutiveRoleCategory
from atlas.alpha.investment_case.executive_compensation_intelligence import extract_executive_compensation_knowledge
from atlas.alpha.investment_case.filing_content_intelligence import extract_filing_content
from atlas.alpha.investment_case.incentive_intelligence import EquityIncentiveKind, IncentiveStructureComponent
from atlas.alpha.investment_case.insider_alignment_intelligence import (
    AlignmentFinding,
    AlignmentFindingKind,
    AlignmentObservationKind,
    OwnershipTrend,
    extract_insider_alignment_knowledge,
)
from atlas.alpha.investment_case.ownership_intelligence import OwnershipKnowledge, extract_ownership_knowledge
from atlas.alpha.investment_case.regulatory_filings import RegulatoryFiling


def _filing(accession: str, filed_at: datetime, form_type: str = "DEF 14A") -> RegulatoryFiling:
    return RegulatoryFiling(
        form_type=form_type, filed_at=filed_at, accession_number=accession, filing_url="https://example.test/doc.htm",
        period_of_report=date(2024, 1, 1),
    )


def _fetcher(html: str):
    def fetch(url: str, headers):
        return html

    return fetch


def _content(accession: str, filed_at: datetime, html: str):
    return extract_filing_content(_filing(accession, filed_at), _fetcher(html))


def _identity(name: str = "Jane Smith") -> ExecutiveIdentity:
    return ExecutiveIdentity(
        name=name, role_category=ExecutiveRoleCategory.CEO, raw_title="Chief Executive Officer", company="Acme Corp",
        start_date=None, end_date=None, is_interim=False, first_observed_date=date(2023, 1, 1),
        last_observed_date=date(2024, 12, 31), source_transcripts=("Q1 2023",), statement_count=3,
    )


_EMPTY_OWNERSHIP = OwnershipKnowledge(categories=(), changes=(), disclosures=(), filings_considered=())


def _empty_compensation():
    return extract_executive_compensation_knowledge(())


_OWNERSHIP_TABLE_HTML = (
    "<table><thead><tr><th>Name</th><th>Percent of Class</th><th>Shares Beneficially Owned</th></tr></thead>"
    "<tbody><tr><td>Jane Smith</td><td>0.5%</td><td>1,000,000</td></tr></tbody></table>"
)

_COMPENSATION_TABLE_HTML = (
    "<table><thead><tr><th>Name</th><th>Salary</th><th>Stock Awards</th></tr></thead>"
    "<tbody><tr><td>Jane Smith</td><td>1,000,000</td><td>5,000,000</td></tr></tbody></table>"
)

_EQUITY_AWARD_TABLE_HTML = (
    "<table><thead><tr><th>Name</th><th>Award Type</th><th>Number of Shares/Units</th></tr></thead>"
    "<tbody><tr><td>Jane Smith</td><td>RSU</td><td>10,000</td></tr></tbody></table>"
)


class TestEmptyInputIsHonest:
    def test_no_executives_yields_no_profiles(self):
        knowledge = extract_insider_alignment_knowledge((), _EMPTY_OWNERSHIP, _empty_compensation())
        assert knowledge.profiles == ()
        assert knowledge.filings_considered == ()

    def test_no_executives_yields_the_no_evidence_finding(self):
        knowledge = extract_insider_alignment_knowledge((), _EMPTY_OWNERSHIP, _empty_compensation())
        assert knowledge.findings == (AlignmentFinding(kind=AlignmentFindingKind.NO_ALIGNMENT_EVIDENCE, evidence_count=0),)

    def test_an_executive_with_no_matching_evidence_anywhere_is_still_a_real_profile(self):
        knowledge = extract_insider_alignment_knowledge((_identity(),), _EMPTY_OWNERSHIP, _empty_compensation())
        assert len(knowledge.profiles) == 1
        profile = knowledge.profiles[0]
        assert profile.ownership.holdings == ()
        assert profile.ownership.trend is OwnershipTrend.INSUFFICIENT_HISTORY
        assert profile.equity_compensation.program is None
        assert profile.equity_compensation.has_equity_awards is False


class TestOwnershipAggregation:
    def test_a_table_sourced_owner_matching_an_executive_by_exact_name_is_linked(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        profile = knowledge.profiles[0]
        assert len(profile.ownership.holdings) == 1
        assert profile.ownership.holdings[0].disclosed_percentage == "0.5%"
        assert profile.ownership.holdings[0].disclosed_share_count == "1,000,000"

    def test_name_matching_is_case_insensitive(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity("JANE SMITH"),), ownership, _empty_compensation())
        assert len(knowledge.profiles[0].ownership.holdings) == 1

    def test_a_non_matching_owner_name_is_never_linked(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity("John Doe"),), ownership, _empty_compensation())
        assert knowledge.profiles[0].ownership.holdings == ()

    def test_a_paragraph_sourced_disclosure_with_no_owner_name_never_links_to_anyone(self):
        html = "<p>Beneficial ownership of our common stock is disclosed below for our directors and executive officers.</p>"
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ownership = extract_ownership_knowledge((content,))
        assert ownership.disclosures and ownership.disclosures[0].owner_name is None
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        assert knowledge.profiles[0].ownership.holdings == ()

    def test_no_fuzzy_matching_a_near_miss_name_is_never_linked(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity("Jane Smith Jr."),), ownership, _empty_compensation())
        assert knowledge.profiles[0].ownership.holdings == ()


class TestHistoricalOwnershipAndTrend:
    def test_two_comparable_disclosures_with_increasing_shares_yields_increasing_trend(self):
        html1 = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,000,000</td></tr></tbody></table>"
        html2 = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,200,000</td></tr></tbody></table>"
        c1 = _content("0001-23-000001", datetime(2023, 3, 1, tzinfo=timezone.utc), html1)
        c2 = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html2)
        ownership = extract_ownership_knowledge((c1, c2))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        profile = knowledge.profiles[0]
        assert profile.ownership.trend is OwnershipTrend.INCREASING
        assert len(profile.ownership_changes) == 1
        assert profile.ownership_changes[0].compared_field == "disclosed_share_count"

    def test_decreasing_shares_yields_decreasing_trend(self):
        html1 = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,200,000</td></tr></tbody></table>"
        html2 = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,000,000</td></tr></tbody></table>"
        c1 = _content("0001-23-000001", datetime(2023, 3, 1, tzinfo=timezone.utc), html1)
        c2 = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html2)
        ownership = extract_ownership_knowledge((c1, c2))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        assert knowledge.profiles[0].ownership.trend is OwnershipTrend.DECREASING

    def test_identical_disclosures_yield_stable_trend(self):
        html = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,000,000</td></tr></tbody></table>"
        c1 = _content("0001-23-000001", datetime(2023, 3, 1, tzinfo=timezone.utc), html)
        c2 = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ownership = extract_ownership_knowledge((c1, c2))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        assert knowledge.profiles[0].ownership.trend is OwnershipTrend.STABLE

    def test_a_single_disclosure_yields_insufficient_history_never_a_guessed_trend(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        profile = knowledge.profiles[0]
        assert profile.ownership.trend is OwnershipTrend.INSUFFICIENT_HISTORY
        assert profile.ownership_changes == ()

    def test_an_unparseable_value_yields_insufficient_history_never_a_guessed_direction(self):
        html1 = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>approximately 1,000,000</td></tr></tbody></table>"
        html2 = "<table><thead><tr><th>Name</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,200,000</td></tr></tbody></table>"
        c1 = _content("0001-23-000001", datetime(2023, 3, 1, tzinfo=timezone.utc), html1)
        c2 = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html2)
        ownership = extract_ownership_knowledge((c1, c2))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        change = knowledge.profiles[0].ownership_changes[0]
        assert change.trend is OwnershipTrend.INSUFFICIENT_HISTORY
        assert change.compared_field is None

    def test_prefers_share_count_over_percentage_when_both_are_comparable(self):
        html1 = "<table><thead><tr><th>Name</th><th>Percent of Class</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>0.5%</td><td>1,000,000</td></tr></tbody></table>"
        html2 = "<table><thead><tr><th>Name</th><th>Percent of Class</th><th>Shares Beneficially Owned</th></tr></thead><tbody><tr><td>Jane Smith</td><td>0.5%</td><td>1,200,000</td></tr></tbody></table>"
        c1 = _content("0001-23-000001", datetime(2023, 3, 1, tzinfo=timezone.utc), html1)
        c2 = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html2)
        ownership = extract_ownership_knowledge((c1, c2))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        change = knowledge.profiles[0].ownership_changes[0]
        assert change.compared_field == "disclosed_share_count"
        assert change.trend is OwnershipTrend.INCREASING

    def test_falls_back_to_percentage_when_share_count_is_not_comparable(self):
        html1 = "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Jane Smith</td><td>0.5%</td></tr></tbody></table>"
        html2 = "<table><thead><tr><th>Name</th><th>Percent of Class</th></tr></thead><tbody><tr><td>Jane Smith</td><td>0.7%</td></tr></tbody></table>"
        c1 = _content("0001-23-000001", datetime(2023, 3, 1, tzinfo=timezone.utc), html1)
        c2 = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html2)
        ownership = extract_ownership_knowledge((c1, c2))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        change = knowledge.profiles[0].ownership_changes[0]
        assert change.compared_field == "disclosed_percentage"
        assert change.trend is OwnershipTrend.INCREASING


class TestEquityCompensationIntegration:
    def test_equity_awards_disclosed_are_linked_via_the_incentive_bridge(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _EQUITY_AWARD_TABLE_HTML)
        compensation = extract_executive_compensation_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), _EMPTY_OWNERSHIP, compensation)
        exposure = knowledge.profiles[0].equity_compensation
        assert exposure.has_equity_awards is True
        assert exposure.equity_incentive_kinds == (EquityIncentiveKind.RSU,)

    def test_cash_only_compensation_is_distinguished_from_equity_compensation(self):
        html = "<table><thead><tr><th>Name</th><th>Salary</th><th>Bonus</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,000,000</td><td>200,000</td></tr></tbody></table>"
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        compensation = extract_executive_compensation_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), _EMPTY_OWNERSHIP, compensation)
        exposure = knowledge.profiles[0].equity_compensation
        assert exposure.has_cash_compensation is True
        assert exposure.has_equity_awards is False
        assert IncentiveStructureComponent.EQUITY_AWARDS not in exposure.disclosed_components
        assert IncentiveStructureComponent.FIXED_SALARY in exposure.disclosed_components

    def test_equity_compensation_present_disclosed_components_include_equity_awards(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _COMPENSATION_TABLE_HTML)
        compensation = extract_executive_compensation_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), _EMPTY_OWNERSHIP, compensation)
        exposure = knowledge.profiles[0].equity_compensation
        assert IncentiveStructureComponent.EQUITY_AWARDS in exposure.disclosed_components

    def test_no_matching_compensation_record_yields_an_honest_absence(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _COMPENSATION_TABLE_HTML)
        compensation = extract_executive_compensation_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity("John Doe"),), _EMPTY_OWNERSHIP, compensation)
        exposure = knowledge.profiles[0].equity_compensation
        assert exposure.program is None
        assert exposure.structure is None
        assert exposure.has_equity_awards is False


class TestAlignmentObservations:
    def test_owns_stock_observation_carries_full_provenance(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        observations = knowledge.profiles[0].observations
        owns_stock = [o for o in observations if o.kind is AlignmentObservationKind.EXECUTIVE_OWNS_STOCK]
        assert len(owns_stock) == 1
        assert owns_stock[0].accession_number == "0001-24-000001"
        assert owns_stock[0].form_type == "DEF 14A"
        assert owns_stock[0].disclosure_source == "def_14a_content"

    def test_no_ownership_observation_when_nothing_is_matched(self):
        knowledge = extract_insider_alignment_knowledge((_identity(),), _EMPTY_OWNERSHIP, _empty_compensation())
        kinds = {o.kind for o in knowledge.profiles[0].observations}
        assert AlignmentObservationKind.EXECUTIVE_HAS_NO_DISCLOSED_OWNERSHIP in kinds
        assert AlignmentObservationKind.EXECUTIVE_OWNS_STOCK not in kinds

    def test_trend_observation_only_emitted_with_real_comparable_history(self):
        content = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        ownership = extract_ownership_knowledge((content,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, _empty_compensation())
        kinds = {o.kind for o in knowledge.profiles[0].observations}
        assert AlignmentObservationKind.OWNERSHIP_INCREASING not in kinds
        assert AlignmentObservationKind.OWNERSHIP_DECREASING not in kinds
        assert AlignmentObservationKind.OWNERSHIP_STABLE not in kinds

    def test_no_observation_is_ever_a_judgment_kind(self):
        """Closed-vocabulary guard: every member name is either a plain
        presence/absence fact or a directional fact -- never a value
        judgment word."""
        forbidden_substrings = ("good", "bad", "trust", "friendly", "risk", "concern", "strong", "weak")
        for kind in AlignmentObservationKind:
            lowered = kind.value.lower()
            assert not any(word in lowered for word in forbidden_substrings), kind


class TestFindings:
    def test_findings_reflect_real_linked_evidence_counts(self):
        oc = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        cc = _content("0001-24-000002", datetime(2024, 3, 1, tzinfo=timezone.utc), _COMPENSATION_TABLE_HTML)
        ownership = extract_ownership_knowledge((oc,))
        compensation = extract_executive_compensation_knowledge((cc,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, compensation)
        finding_kinds = {f.kind: f.evidence_count for f in knowledge.findings}
        assert finding_kinds[AlignmentFindingKind.OWNERSHIP_EVIDENCE_LINKED] == 1
        assert finding_kinds[AlignmentFindingKind.EQUITY_COMPENSATION_EVIDENCE_LINKED] == 1


class TestFilingsConsidered:
    def test_filings_considered_is_the_union_of_both_sources(self):
        oc = _content("0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _OWNERSHIP_TABLE_HTML)
        cc = _content("0001-24-000002", datetime(2024, 3, 1, tzinfo=timezone.utc), _COMPENSATION_TABLE_HTML)
        ownership = extract_ownership_knowledge((oc,))
        compensation = extract_executive_compensation_knowledge((cc,))
        knowledge = extract_insider_alignment_knowledge((_identity(),), ownership, compensation)
        assert set(knowledge.filings_considered) == {"0001-24-000001", "0001-24-000002"}


class TestArchitectureBoundary:
    def test_module_never_imports_html_parser(self):
        import atlas.alpha.investment_case.insider_alignment_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        assert "html.parser" not in text
        assert "HTMLParser" not in text

    def test_module_never_imports_the_always_empty_incentive_entry_point(self):
        """`incentive_intelligence.extract_incentive_intelligence` is
        always empty (Sprint 12) -- this module must use Sprint 20's own
        real bridge functions instead."""
        import atlas.alpha.investment_case.insider_alignment_intelligence as module
        assert not hasattr(module, "extract_incentive_intelligence")

    def test_ownership_intelligence_source_is_never_modified_by_this_test_run(self):
        from atlas.alpha.investment_case.ownership_intelligence import extract_ownership_knowledge as f
        result = f(())
        assert result.disclosures == ()
        assert result.categories == ()

    def test_executive_compensation_intelligence_source_is_never_modified_by_this_test_run(self):
        result = _empty_compensation()
        assert result.records == ()

    def test_no_score_field_exists_anywhere_in_the_knowledge_model(self):
        import atlas.alpha.investment_case.insider_alignment_intelligence as module
        import dataclasses
        for name in module.__all__:
            obj = getattr(module, name)
            if dataclasses.is_dataclass(obj):
                for field in dataclasses.fields(obj):
                    lowered = field.name.lower()
                    assert "score" not in lowered
                    assert "rank" not in lowered
                    assert "rating" not in lowered
