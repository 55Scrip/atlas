"""Tests for `atlas.alpha.investment_case.capital_allocation_intelligence`
(Capability Expansion Sprint 4, Phases 1 + 3 + 4 + 5).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.capital_allocation_intelligence import (
    AcquisitionBehavior,
    BuybackConsistency,
    CapitalAllocationTrendMetric,
    DebtDiscipline,
    DividendContinuity,
    ShareholderReturnPolicy,
    TrendDirection,
    assess_buyback_consistency,
    assess_dividend_continuity,
    assess_management_capital_allocation,
    compute_capital_allocation_trends,
    extract_capital_allocation_history,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

_EVALUATED_AT = datetime(2026, 8, 22, tzinfo=timezone.utc)


def _period(year: int, **metadata):
    document = RawBusinessDocument(
        identifier=f"AAPL:FY:{year}-12-31",
        company="AAPL",
        source_kind="financial_statement",
        published_at=datetime(year + 1, 2, 15, tzinfo=timezone.utc),
        provider_id="sec_edgar",
        raw_reference="https://example.test/10k",
        content_hash=f"hash-{year}",
        language="en",
        period_start=date(year, 1, 1),
        period_end=date(year, 12, 31),
        metadata={**metadata, "currency": "USD"},
    )
    result = ingest(document, evaluated_at=_EVALUATED_AT)
    assert isinstance(result, IngestedRecord)
    return result.record


class TestExtraction:
    def test_no_records_produces_empty_history(self):
        history = extract_capital_allocation_history(())
        assert history.periods == ()

    def test_periods_are_chronological(self):
        records = (_period(2022, capital_expenditure=100.0), _period(2020, capital_expenditure=80.0), _period(2021, capital_expenditure=90.0))
        history = extract_capital_allocation_history(records)
        assert [p.period_end for p in history.periods] == [date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31)]

    def test_every_field_is_read_from_real_metadata(self):
        records = (
            _period(
                2023, capital_expenditure=100.0, dividends=50.0, share_buybacks=200.0, treasury_shares_acquired=5_000_000.0,
                share_issuance=10.0, shares_outstanding=1_000_000_000.0, debt_issuance=300.0, debt_repayment=250.0,
                total_debt=1000.0, acquisitions=400.0, disposals=20.0, investing_cash_flow=-350.0, sec_form="10-K",
            ),
        )
        period = extract_capital_allocation_history(records).periods[0]
        assert period.capital_expenditure == 100.0
        assert period.dividends == 50.0
        assert period.share_buybacks == 200.0
        assert period.treasury_shares_acquired == 5_000_000.0
        assert period.share_issuance == 10.0
        assert period.shares_outstanding == 1_000_000_000.0
        assert period.debt_issuance == 300.0
        assert period.debt_repayment == 250.0
        assert period.total_debt == 1000.0
        assert period.acquisitions == 400.0
        assert period.disposals == 20.0
        assert period.investment_activity == -350.0
        assert period.currency == "USD"
        assert period.accounting_basis == "10-K"
        assert period.source_reference == "https://example.test/10k"

    def test_maintenance_and_growth_capex_are_always_none(self):
        records = (_period(2023, capital_expenditure=100.0),)
        period = extract_capital_allocation_history(records).periods[0]
        assert period.maintenance_capex is None
        assert period.growth_capex is None


class TestTrendIntelligence:
    def test_fewer_than_three_periods_is_insufficient(self):
        records = (_period(2022, shares_outstanding=1000.0), _period(2023, shares_outstanding=1100.0))
        observations = compute_capital_allocation_trends(extract_capital_allocation_history(records))
        share_count = next(o for o in observations if o.metric is CapitalAllocationTrendMetric.SHARE_COUNT)
        assert share_count.direction is TrendDirection.INSUFFICIENT_DATA

    def test_rising_share_count_is_dilution(self):
        records = tuple(_period(2020 + i, shares_outstanding=1000.0 + i * 200.0) for i in range(4))
        observations = compute_capital_allocation_trends(extract_capital_allocation_history(records))
        share_count = next(o for o in observations if o.metric is CapitalAllocationTrendMetric.SHARE_COUNT)
        assert share_count.direction is TrendDirection.RISING

    def test_falling_debt_trajectory_is_deleveraging(self):
        records = tuple(_period(2020 + i, total_debt=1000.0 - i * 200.0) for i in range(4))
        observations = compute_capital_allocation_trends(extract_capital_allocation_history(records))
        debt_trend = next(o for o in observations if o.metric is CapitalAllocationTrendMetric.DEBT_TRAJECTORY)
        assert debt_trend.direction is TrendDirection.FALLING

    def test_rising_capex_is_increasing_investment_intensity(self):
        records = tuple(_period(2020 + i, capital_expenditure=50.0 + i * 40.0) for i in range(4))
        observations = compute_capital_allocation_trends(extract_capital_allocation_history(records))
        capex_trend = next(o for o in observations if o.metric is CapitalAllocationTrendMetric.CAPITAL_EXPENDITURE_TREND)
        assert capex_trend.direction is TrendDirection.RISING


class TestDividendContinuity:
    def test_fewer_than_two_known_periods_is_insufficient(self):
        records = (_period(2023, dividends=50.0),)
        assert assess_dividend_continuity(extract_capital_allocation_history(records)) is DividendContinuity.INSUFFICIENT_DATA

    def test_never_paying_is_never_paid(self):
        records = (_period(2022, dividends=0.0), _period(2023, dividends=0.0))
        assert assess_dividend_continuity(extract_capital_allocation_history(records)) is DividendContinuity.NEVER_PAID

    def test_zero_after_positive_is_suspended(self):
        records = (_period(2021, dividends=50.0), _period(2022, dividends=60.0), _period(2023, dividends=0.0))
        assert assess_dividend_continuity(extract_capital_allocation_history(records)) is DividendContinuity.SUSPENDED

    def test_ongoing_payments_are_consistently_paid(self):
        records = (_period(2022, dividends=50.0), _period(2023, dividends=55.0))
        assert assess_dividend_continuity(extract_capital_allocation_history(records)) is DividendContinuity.CONSISTENTLY_PAID


class TestBuybackConsistency:
    def test_fewer_than_two_known_periods_is_insufficient(self):
        records = (_period(2023, share_buybacks=100.0),)
        assert assess_buyback_consistency(extract_capital_allocation_history(records)) is BuybackConsistency.INSUFFICIENT_DATA

    def test_buybacks_every_period_is_consistent(self):
        records = (_period(2022, share_buybacks=100.0), _period(2023, share_buybacks=150.0))
        assert assess_buyback_consistency(extract_capital_allocation_history(records)) is BuybackConsistency.CONSISTENT

    def test_no_buybacks_ever_is_none(self):
        records = (_period(2022, share_buybacks=0.0), _period(2023, share_buybacks=0.0))
        assert assess_buyback_consistency(extract_capital_allocation_history(records)) is BuybackConsistency.NONE

    def test_some_periods_only_is_intermittent(self):
        records = (_period(2022, share_buybacks=0.0), _period(2023, share_buybacks=100.0))
        assert assess_buyback_consistency(extract_capital_allocation_history(records)) is BuybackConsistency.INTERMITTENT


class TestManagementCapitalAllocationKnowledge:
    def test_no_data_is_insufficient_across_every_dimension(self):
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(()))
        assert knowledge.reinvestment_discipline is TrendDirection.INSUFFICIENT_DATA
        assert knowledge.shareholder_return_policy is ShareholderReturnPolicy.INSUFFICIENT_DATA
        assert knowledge.acquisition_behavior is AcquisitionBehavior.INSUFFICIENT_DATA
        assert knowledge.debt_discipline is DebtDiscipline.INSUFFICIENT_DATA

    def test_active_shareholder_return_policy_when_currently_paying(self):
        records = (_period(2023, dividends=50.0, share_buybacks=0.0),)
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.shareholder_return_policy is ShareholderReturnPolicy.ACTIVE

    def test_limited_shareholder_return_policy_when_historically_active_but_not_now(self):
        records = (_period(2022, dividends=50.0, share_buybacks=0.0), _period(2023, dividends=0.0, share_buybacks=0.0))
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.shareholder_return_policy is ShareholderReturnPolicy.LIMITED

    def test_no_shareholder_return_policy_when_never_active(self):
        records = (_period(2022, dividends=0.0, share_buybacks=0.0), _period(2023, dividends=0.0, share_buybacks=0.0))
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.shareholder_return_policy is ShareholderReturnPolicy.NONE

    def test_active_acquirer_when_acquisitions_in_most_periods(self):
        records = (_period(2021, acquisitions=100.0), _period(2022, acquisitions=200.0), _period(2023, acquisitions=0.0))
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.acquisition_behavior is AcquisitionBehavior.ACTIVE_ACQUIRER

    def test_opportunistic_when_acquisitions_in_a_minority_of_periods(self):
        records = (
            _period(2020, acquisitions=0.0), _period(2021, acquisitions=0.0), _period(2022, acquisitions=0.0),
            _period(2023, acquisitions=100.0),
        )
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.acquisition_behavior is AcquisitionBehavior.OPPORTUNISTIC

    def test_disciplined_debt_when_repayment_matches_issuance(self):
        records = (_period(2023, debt_issuance=100.0, debt_repayment=90.0),)
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.debt_discipline is DebtDiscipline.DISCIPLINED

    def test_disciplined_debt_when_no_debt_issued_at_all(self):
        records = (_period(2023, debt_issuance=0.0, debt_repayment=0.0),)
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.debt_discipline is DebtDiscipline.DISCIPLINED

    def test_accumulating_debt_when_repayment_is_far_below_issuance(self):
        records = (_period(2023, debt_issuance=1000.0, debt_repayment=50.0),)
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.debt_discipline is DebtDiscipline.ACCUMULATING

    def test_reinvestment_discipline_matches_capex_trend(self):
        records = tuple(_period(2020 + i, capital_expenditure=50.0 + i * 40.0) for i in range(4))
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.reinvestment_discipline is TrendDirection.RISING

    def test_financing_strategy_matches_debt_trend(self):
        records = tuple(_period(2020 + i, total_debt=1000.0 - i * 200.0) for i in range(4))
        knowledge = assess_management_capital_allocation(extract_capital_allocation_history(records))
        assert knowledge.financing_strategy is TrendDirection.FALLING
