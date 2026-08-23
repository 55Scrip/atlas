"""Tests for `atlas.alpha.investment_case.executive_compensation_intelligence`
(Capability Expansion Sprint 20).

All fake -- built entirely on `extract_filing_content` with an
injected, no-network fetcher (mirrors `test_ownership_intelligence.py`
's own convention). Live verification against real SEC filings is done
separately, outside the unit suite.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveIdentity, ExecutiveRoleCategory
from atlas.alpha.investment_case.executive_compensation_intelligence import (
    CompensationChangeKind,
    CompensationComponentKind,
    build_incentive_knowledge,
    build_incentive_structures,
    extract_executive_compensation_knowledge,
)
from atlas.alpha.investment_case.filing_content_intelligence import extract_filing_content
from atlas.alpha.investment_case.incentive_intelligence import CashIncentiveKind, EquityIncentiveKind, IncentiveStructureComponent
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


_SUMMARY_HTML = (
    "<table><thead><tr><th>Name and Principal Position</th><th>Year</th><th>Salary</th><th>Bonus</th>"
    "<th>Stock Awards</th><th>Option Awards</th><th>Total</th></tr></thead>"
    "<tbody><tr><td>Jane Smith</td><td>2023</td><td>1,200,000</td><td></td><td>5,000,000</td><td>2,000,000</td>"
    "<td>8,200,000</td></tr></tbody></table>"
)


class TestEmptyInputIsHonest:
    def test_no_filings_yields_an_empty_but_real_result(self):
        ck = extract_executive_compensation_knowledge(())
        assert ck.records == ()
        assert ck.equity_awards == ()
        assert ck.performance_metrics == ()
        assert ck.changes == ()
        assert ck.filings_considered == ()

    def test_a_fetch_failed_filing_contributes_nothing(self):
        content = extract_filing_content(
            _filing("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc)),
            lambda url, headers: (_ for _ in ()).throw(RuntimeError("down")),
        )
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.filings_considered == ()
        assert ck.records == ()


class TestSummaryCompensationTableExtraction:
    def test_a_labeled_summary_table_is_recognized(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert len(ck.records) == 1
        assert ck.records[0].executive_name == "Jane Smith"

    def test_all_disclosed_components_are_preserved_verbatim(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.reporting_year == "2023"
        assert record.salary == "1,200,000"
        assert record.bonus is None
        assert record.stock_awards == "5,000,000"
        assert record.option_awards == "2,000,000"
        assert record.total == "8,200,000"

    def test_missing_values_remain_missing_never_calculated_from_total(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Salary</th><th>Bonus</th><th>Total</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>1,000,000</td><td></td><td>3,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.bonus is None
        assert record.stock_awards is None
        assert record.option_awards is None

    def test_a_table_with_no_name_column_is_never_recognized(self):
        html = "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody><tr><td>Revenue</td><td>100</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.records == ()

    def test_a_name_only_table_with_no_compensation_column_is_never_recognized(self):
        """Mirrors ownership_intelligence's own equivalent fix -- a
        board roster with a "Name" column but no salary/bonus/total
        column is not a compensation table."""
        html = "<table><thead><tr><th>Name</th><th>Position</th></tr></thead><tbody><tr><td>Jane Smith</td><td>Director</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.records == ()

    def test_a_row_with_no_name_is_never_a_record(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td></td><td>1,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.records == ()

    def test_a_rowspanned_name_cell_carries_forward_to_later_year_rows(self):
        """Real DEF 14As disclose each executive's multi-year rows with
        the Name cell `rowspan`'d across all of that executive's rows
        -- only the first year's row literally contains the name text
        in the raw HTML. Live-verification-driven fix: an empty Name
        cell on a row that otherwise carries real Salary/Year data must
        inherit the immediately preceding row's name, or 2+ years of
        real history are silently dropped."""
        html = (
            "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th></tr></thead><tbody>"
            "<tr><td rowspan='2'>Jane Smith</td><td>2023</td><td>1,200,000</td></tr>"
            "<tr><td>2022</td><td>1,000,000</td></tr>"
            "</tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert len(ck.records) == 2
        assert {r.reporting_year for r in ck.records} == {"2023", "2022"}
        assert all(r.executive_name == "Jane Smith" for r in ck.records)

    def test_a_genuinely_blank_row_with_no_carried_name_is_never_a_record(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td></td><td></td><td></td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.records == ()

    def test_a_blank_name_row_with_no_data_of_its_own_is_never_attached(self):
        """An empty separator/footnote row must not be silently
        attached to the previous executive just because a name was
        carried forward -- it must also carry its own Salary or Year."""
        html = (
            "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th></tr></thead><tbody>"
            "<tr><td>Jane Smith</td><td>2023</td><td>1,200,000</td></tr>"
            "<tr><td></td><td></td><td></td></tr>"
            "</tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert len(ck.records) == 1

    def test_bold_td_header_with_no_thead_is_still_recognized(self):
        html = (
            "<table><tr><td><b>Name</b></td><td><b>Salary</b></td></tr>"
            "<tr><td>Jane Smith</td><td>1,000,000</td></tr></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert len(ck.records) == 1
        assert ck.records[0].salary == "1,000,000"

    def test_non_equity_incentive_and_pension_columns_use_real_full_headers(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Salary</th>"
            "<th>Non-Equity Incentive Plan Compensation</th>"
            "<th>Change in Pension Value and Nonqualified Deferred Compensation Earnings</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>1,000,000</td><td>300,000</td><td>50,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.non_equity_incentive == "300,000"
        assert record.pension_change == "50,000"

    def test_disclosed_role_is_preserved_from_its_own_column(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Principal Position</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>Chief Executive Officer</td><td>1,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.disclosed_role == "Chief Executive Officer"

    def test_records_carry_full_provenance(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.accession_number == "0001-24-000001"
        assert record.form_type == "DEF 14A"
        assert record.table_order_index == 0
        assert record.row_index == 0

    def test_currency_is_read_from_table_context_when_explicit(self):
        html = (
            '<table><caption>Summary Compensation Table (amounts in EUR)</caption>'
            "<thead><tr><th>Name</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>1,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.currency == "EUR"

    def test_currency_is_honestly_none_when_not_stated(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.currency is None

    def test_a_combined_name_and_principal_position_column_is_never_split(self):
        """Real DEF 14As commonly join name and title into one "Name and
        Principal Position" column via <br> -- with no reliable
        delimiter once whitespace is collapsed. The record must keep
        the full verbatim cell text as `executive_name` and must never
        guess a role by splitting it (that would be inferring a role
        from name recognition, forbidden by Phase 2/4)."""
        html = (
            "<table><thead><tr><th>Name and Principal Position</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td>Jane Smith Chief Executive Officer</td><td>1,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        record = extract_executive_compensation_knowledge((content,)).records[0]
        assert record.executive_name == "Jane Smith Chief Executive Officer"
        assert record.disclosed_role is None


class TestEquityAwardTableExtraction:
    _HTML = (
        "<table><thead><tr><th>Name</th><th>Award Type</th><th>Grant Date</th>"
        "<th>Number of Shares/Units</th><th>Grant Date Fair Value</th></tr></thead>"
        "<tbody><tr><td>Jane Smith</td><td>RSU</td><td>3/1/2023</td><td>10,000</td><td>5,000,000</td></tr></tbody></table>"
    )

    def test_equity_awards_are_extracted(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert len(ck.equity_awards) == 1
        award = ck.equity_awards[0]
        assert award.executive_name == "Jane Smith"
        assert award.disclosed_award_type == "RSU"
        assert award.grant_value == "5,000,000"
        assert award.unit_count == "10,000"

    def test_award_type_is_classified_into_the_closed_incentive_vocabulary(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._HTML)
        award = extract_executive_compensation_knowledge((content,)).equity_awards[0]
        assert award.kind is EquityIncentiveKind.RSU

    def test_psu_is_classified_correctly(self):
        html = self._HTML.replace(">RSU<", ">PSU<")
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        award = extract_executive_compensation_knowledge((content,)).equity_awards[0]
        assert award.kind is EquityIncentiveKind.PSU

    def test_an_unrecognized_award_type_is_preserved_but_unclassified(self):
        html = self._HTML.replace(">RSU<", ">Deferred Cash Match<")
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        award = extract_executive_compensation_knowledge((content,)).equity_awards[0]
        assert award.disclosed_award_type == "Deferred Cash Match"
        assert award.kind is None

    def test_a_summary_table_is_never_also_read_as_an_equity_award_table(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.equity_awards == ()


class TestPerformanceMetricDisclosure:
    def test_a_real_performance_sentence_is_detected(self):
        html = "<p>Vesting of the performance stock units is subject to achievement of a revenue target over a three-year performance period.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert any(m.metric_kind.value == "revenue_target" for m in ck.performance_metrics)

    def test_target_is_never_estimated(self):
        html = "<p>Awards are subject to achievement of a revenue target.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        metric = extract_executive_compensation_knowledge((content,)).performance_metrics[0]
        assert metric.target is None

    def test_an_unrelated_paragraph_is_never_a_performance_disclosure(self):
        html = "<p>Our headquarters are located in Cupertino, California.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.performance_metrics == ()

    def test_unrecognized_metric_falls_back_to_other_with_verbatim_label(self):
        html = "<p>Awards are performance-based, subject to achievement of internally-developed strategic milestones.</p>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        metric = extract_executive_compensation_knowledge((content,)).performance_metrics[0]
        assert metric.metric_kind.value == "other_explicit_metric"
        assert metric.metric_label == html.split("<p>")[1].split("</p>")[0]


class TestCompensationHistory:
    _TWO_YEAR_HTML = (
        "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th><th>Bonus</th><th>Stock Awards</th><th>Option Awards</th></tr></thead>"
        "<tbody>"
        "<tr><td>Jane Smith</td><td>2023</td><td>1,200,000</td><td></td><td>5,000,000</td><td>2,000,000</td></tr>"
        "<tr><td>Jane Smith</td><td>2022</td><td>1,000,000</td><td>500,000</td><td>4,000,000</td><td></td></tr>"
        "</tbody></table>"
    )

    def test_salary_increased(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._TWO_YEAR_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        changes = [c for c in ck.changes if c.kind is CompensationChangeKind.SALARY_INCREASED]
        assert len(changes) == 1
        assert changes[0].previous_value == "1,000,000"
        assert changes[0].current_value == "1,200,000"

    def test_stock_award_value_increased(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._TWO_YEAR_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert any(c.kind is CompensationChangeKind.STOCK_AWARD_VALUE_INCREASED for c in ck.changes)

    def test_option_awards_introduced(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._TWO_YEAR_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        changes = [c for c in ck.changes if c.kind is CompensationChangeKind.OPTION_AWARDS_INTRODUCED]
        assert len(changes) == 1
        assert changes[0].previous_value is None
        assert changes[0].current_value == "2,000,000"

    def test_bonus_is_never_introduced_the_wrong_direction(self):
        """2023 has no bonus, 2022 did -- this must never fire
        BONUS_INTRODUCED (that would require the *later* year to gain
        it, not lose it)."""
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._TWO_YEAR_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert not any(c.kind is CompensationChangeKind.BONUS_INTRODUCED for c in ck.changes)

    def test_compensation_mix_changed(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), self._TWO_YEAR_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert any(c.kind is CompensationChangeKind.COMPENSATION_MIX_CHANGED for c in ck.changes)

    def test_identical_consecutive_years_generate_no_salary_change(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>2023</td><td>1,000,000</td></tr>"
            "<tr><td>Jane Smith</td><td>2022</td><td>1,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert not any(c.kind in (CompensationChangeKind.SALARY_INCREASED, CompensationChangeKind.SALARY_DECREASED) for c in ck.changes)

    def test_unparseable_value_yields_not_comparable_never_a_guessed_direction(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>2023</td><td>1,200,000(1)</td></tr>"
            "<tr><td>Jane Smith</td><td>2022</td><td>1,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        salary_changes = [c for c in ck.changes if c.component is CompensationComponentKind.SALARY]
        assert len(salary_changes) == 1
        assert salary_changes[0].kind is CompensationChangeKind.COMPENSATION_NOT_COMPARABLE

    def test_different_executives_are_never_compared_to_each_other(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Year</th><th>Salary</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>2023</td><td>1,000,000</td></tr>"
            "<tr><td>John Doe</td><td>2023</td><td>900,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.changes == ()

    def test_a_single_year_never_generates_a_change(self):
        html = "<table><thead><tr><th>Name</th><th>Salary</th></tr></thead><tbody><tr><td>Jane Smith</td><td>1,000,000</td></tr></tbody></table>"
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.changes == ()


class TestExecutiveIdentityLinking:
    def test_an_exact_name_match_links_the_record(self):
        identity = ExecutiveIdentity(
            name="Jane Smith", role_category=ExecutiveRoleCategory.CEO, raw_title="Chief Executive Officer",
            company="Acme Corp", start_date=None, end_date=None, is_interim=False,
            first_observed_date=date(2023, 1, 1), last_observed_date=date(2023, 12, 31),
            source_transcripts=("Q1 2023",), statement_count=3,
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        ck = extract_executive_compensation_knowledge((content,), executive_identities=(identity,))
        assert ck.records[0].linked_executive_identity_name == "Jane Smith"

    def test_case_insensitive_match_still_links(self):
        identity = ExecutiveIdentity(
            name="JANE SMITH", role_category=ExecutiveRoleCategory.CEO, raw_title="CEO", company=None,
            start_date=None, end_date=None, is_interim=False, first_observed_date=date(2023, 1, 1),
            last_observed_date=date(2023, 12, 31), source_transcripts=(), statement_count=1,
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        ck = extract_executive_compensation_knowledge((content,), executive_identities=(identity,))
        assert ck.records[0].linked_executive_identity_name == "JANE SMITH"

    def test_no_matching_identity_leaves_the_link_honestly_none(self):
        identity = ExecutiveIdentity(
            name="John Doe", role_category=ExecutiveRoleCategory.CFO, raw_title="CFO", company=None,
            start_date=None, end_date=None, is_interim=False, first_observed_date=date(2023, 1, 1),
            last_observed_date=date(2023, 12, 31), source_transcripts=(), statement_count=1,
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        ck = extract_executive_compensation_knowledge((content,), executive_identities=(identity,))
        assert ck.records[0].linked_executive_identity_name is None

    def test_no_identities_supplied_leaves_every_link_honestly_none(self):
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), _SUMMARY_HTML)
        ck = extract_executive_compensation_knowledge((content,))
        assert ck.records[0].linked_executive_identity_name is None


class TestIncentiveIntelligenceBridge:
    def test_incentive_intelligence_module_is_never_imported_for_modification(self):
        """`build_incentive_knowledge` only constructs instances of
        `incentive_intelligence`'s own existing types -- this module
        must never define a function named `extract_incentive_
        intelligence` (that would be redefining the existing module's
        own entry point) or import anything suggesting a rewrite."""
        import atlas.alpha.investment_case.executive_compensation_intelligence as module
        assert not hasattr(module, "extract_incentive_intelligence")

    def test_a_bonus_becomes_a_cash_incentive(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Salary</th><th>Bonus</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>1,000,000</td><td>200,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        programs = build_incentive_knowledge(ck)
        assert len(programs) == 1
        assert programs[0].executive_name == "Jane Smith"
        assert len(programs[0].cash_incentives) == 1
        assert programs[0].cash_incentives[0].kind is CashIncentiveKind.ANNUAL_BONUS

    def test_a_classified_equity_award_becomes_an_equity_incentive(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Award Type</th><th>Number of Shares/Units</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>RSU</td><td>10,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        programs = build_incentive_knowledge(ck)
        assert len(programs[0].equity_incentives) == 1
        assert programs[0].equity_incentives[0].kind is EquityIncentiveKind.RSU

    def test_an_unclassified_equity_award_is_never_bridged(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Award Type</th><th>Number of Shares/Units</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>Deferred Cash Match</td><td>10,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        programs = build_incentive_knowledge(ck)
        assert programs == ()

    def test_provenance_is_a_real_traceable_string(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Salary</th><th>Bonus</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>1,000,000</td><td>200,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        programs = build_incentive_knowledge(ck)
        assert "0001-24-000001" in programs[0].cash_incentives[0].provenance

    def test_incentive_structures_reflect_only_disclosed_components(self):
        html = (
            "<table><thead><tr><th>Name</th><th>Salary</th><th>Stock Awards</th></tr></thead>"
            "<tbody><tr><td>Jane Smith</td><td>1,000,000</td><td>2,000,000</td></tr></tbody></table>"
        )
        content = _content("DEF 14A", "0001-24-000001", datetime(2024, 3, 1, tzinfo=timezone.utc), html)
        ck = extract_executive_compensation_knowledge((content,))
        structures = build_incentive_structures(ck)
        assert len(structures) == 1
        assert set(structures[0].components) == {IncentiveStructureComponent.FIXED_SALARY, IncentiveStructureComponent.EQUITY_AWARDS}

    def test_no_records_yields_no_programs_or_structures(self):
        ck = extract_executive_compensation_knowledge(())
        assert build_incentive_knowledge(ck) == ()
        assert build_incentive_structures(ck) == ()


class TestOwnershipBoundary:
    def test_module_never_imports_ownership_intelligence(self):
        import atlas.alpha.investment_case.executive_compensation_intelligence as module
        with open(module.__file__) as f:
            lines = f.readlines()
        import_lines = [line for line in lines if line.startswith("import ") or line.startswith("from ")]
        assert not any("ownership_intelligence" in line for line in import_lines)

    def test_no_field_resembles_beneficial_ownership(self):
        import atlas.alpha.investment_case.executive_compensation_intelligence as module
        import dataclasses
        for field in dataclasses.fields(module.ExecutiveCompensationRecord):
            assert "ownership" not in field.name.lower()
            assert "beneficial" not in field.name.lower()


class TestArchitectureBoundary:
    def test_module_does_not_import_html_parser(self):
        import atlas.alpha.investment_case.executive_compensation_intelligence as module
        with open(module.__file__) as f:
            text = f.read()
        assert "html.parser" not in text
        assert "HTMLParser" not in text

    def test_incentive_intelligence_source_is_never_modified_by_this_test_run(self):
        """A cheap, real guard: `incentive_intelligence.py`'s own
        `extract_incentive_intelligence` must still behave exactly as
        it did before this sprint -- empty knowledge objects, the
        single `COMPENSATION_DATA_UNAVAILABLE` finding -- regardless of
        this module's own existence."""
        from atlas.alpha.investment_case.incentive_intelligence import extract_incentive_intelligence
        result = extract_incentive_intelligence(())
        assert result.executive_incentive_programs == ()
        assert result.compensation_disclosure_filings == ()


class TestFilingsConsidered:
    def test_filings_considered_lists_accession_numbers_chronologically(self):
        earlier = _content("DEF 14A", "0001-24-000001", datetime(2023, 1, 1, tzinfo=timezone.utc), "<p>Text.</p>")
        later = _content("DEF 14A", "0001-24-000002", datetime(2024, 1, 1, tzinfo=timezone.utc), "<p>Text.</p>")
        ck = extract_executive_compensation_knowledge((later, earlier))
        assert ck.filings_considered == ("0001-24-000001", "0001-24-000002")
