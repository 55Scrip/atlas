"""Tests for `atlas.analysis_engine.business_data.completeness
.assess_data_completeness` (Company Data Foundation v1) -- a pure
structural checklist, never a score."""
from __future__ import annotations

from datetime import date

from atlas.analysis_engine.business_data.completeness import assess_data_completeness
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from tests.unit.analysis_engine.business_data._fixtures import EVALUATED_AT, build_raw_document


def _record(**kwargs):
    result = ingest(build_raw_document(**kwargs), evaluated_at=EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestEmptyRecords:
    def test_no_records_at_all_is_not_minimally_complete(self):
        completeness = assess_data_completeness(())
        assert completeness.has_company_profile is False
        assert completeness.has_financial_statements is False
        assert completeness.financial_statement_period_count == 0
        assert completeness.has_market_snapshot is False
        assert completeness.is_minimally_complete is False


class TestCompanyProfileOnly:
    def test_a_company_profile_record_alone_is_minimally_complete(self):
        record = _record(identifier="profile", source_kind="company_profile", metadata={"name": "Test Co"})
        completeness = assess_data_completeness((record,))
        assert completeness.has_company_profile is True
        assert completeness.has_financial_statements is False
        assert completeness.is_minimally_complete is True


class TestFinancialStatementsOnly:
    def test_one_financial_statement_period_is_minimally_complete(self):
        record = _record(
            identifier="fy2024",
            source_kind="financial_statement",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            metadata={"revenue": 1000.0},
        )
        completeness = assess_data_completeness((record,))
        assert completeness.has_financial_statements is True
        assert completeness.financial_statement_period_count == 1
        assert completeness.is_minimally_complete is True

    def test_period_count_reflects_distinct_periods_not_record_count(self):
        r1 = _record(
            identifier="fy2023",
            source_kind="financial_statement",
            period_start=date(2023, 1, 1),
            period_end=date(2023, 12, 31),
            metadata={"revenue": 900.0},
        )
        r2 = _record(
            identifier="fy2024",
            source_kind="financial_statement",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            metadata={"revenue": 1000.0},
        )
        completeness = assess_data_completeness((r1, r2))
        assert completeness.financial_statement_period_count == 2


class TestMarketSnapshotAlone:
    """The exact scenario the sprint names: a company with only a
    stray market snapshot and nothing else must NOT be minimally
    complete -- the whole reason this predicate exists."""

    def test_a_market_snapshot_alone_is_not_minimally_complete(self):
        record = _record(
            identifier="snapshot",
            source_kind="market_data_snapshot",
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 1),
            metadata={"share_price": 100.0},
        )
        completeness = assess_data_completeness((record,))
        assert completeness.has_market_snapshot is True
        assert completeness.has_company_profile is False
        assert completeness.has_financial_statements is False
        assert completeness.is_minimally_complete is False


class TestFullCoverage:
    def test_profile_plus_statements_plus_market_is_minimally_complete(self):
        profile = _record(identifier="profile", source_kind="company_profile", metadata={"name": "Test Co"})
        statement = _record(
            identifier="fy2024",
            source_kind="financial_statement",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            metadata={"revenue": 1000.0},
        )
        snapshot = _record(
            identifier="snapshot",
            source_kind="market_data_snapshot",
            period_start=date(2026, 8, 1),
            period_end=date(2026, 8, 1),
            metadata={"share_price": 100.0},
        )
        completeness = assess_data_completeness((profile, statement, snapshot))
        assert completeness.has_company_profile is True
        assert completeness.has_financial_statements is True
        assert completeness.has_market_snapshot is True
        assert completeness.is_minimally_complete is True


class TestDeterminism:
    def test_identical_records_produce_a_deeply_equal_result(self):
        record = _record(identifier="profile", source_kind="company_profile", metadata={"name": "Test Co"})
        assert assess_data_completeness((record,)) == assess_data_completeness((record,))

    def test_never_a_numeric_score(self):
        completeness = assess_data_completeness(())
        assert not hasattr(completeness, "score")
