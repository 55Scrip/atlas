"""Tests for `atlas.alpha.investment_case.financial_statement_intelligence`
(Capability Expansion Sprint 3, Phases 1 + 3 + 4 + 5).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.financial_statement_intelligence import (
    ConsistencyLevel,
    FinancialHealthTier,
    FinancialTrendMetric,
    SolvencyTier,
    TrendDirection,
    assess_financial_health,
    compute_cash_flow_consistency,
    compute_trend_intelligence,
    extract_financial_statement_history,
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
        history = extract_financial_statement_history(())
        assert history.income_statements == ()
        assert history.balance_sheets == ()
        assert history.cash_flow_statements == ()
        assert history.segments.segments == ()

    def test_periods_are_chronological(self):
        records = (
            _period(2023, revenue=1200.0),
            _period(2021, revenue=1000.0),
            _period(2022, revenue=1100.0),
        )
        history = extract_financial_statement_history(records)
        assert [p.period_end for p in history.income_statements] == [date(2021, 12, 31), date(2022, 12, 31), date(2023, 12, 31)]

    def test_income_statement_fields_and_margins(self):
        records = (_period(2023, revenue=1000.0, gross_profit=400.0, operating_income=200.0, net_income=150.0, eps=2.5, ebitda=250.0),)
        period = extract_financial_statement_history(records).income_statements[0]
        assert period.revenue == 1000.0
        assert period.gross_profit == 400.0
        assert period.operating_income == 200.0
        assert period.ebitda == 250.0
        assert period.net_income == 150.0
        assert period.eps == 2.5
        assert period.gross_margin == 0.4
        assert period.operating_margin == 0.2
        assert period.net_margin == 0.15

    def test_margins_are_none_without_revenue(self):
        records = (_period(2023, gross_profit=400.0),)
        period = extract_financial_statement_history(records).income_statements[0]
        assert period.gross_margin is None

    def test_balance_sheet_fields(self):
        records = (
            _period(
                2023, revenue=1000.0, cash=500.0, total_debt=300.0, equity=700.0, current_assets=600.0,
                current_liabilities=200.0, working_capital=400.0, total_assets=1200.0, tangible_assets=1000.0,
                intangible_assets=200.0,
            ),
        )
        period = extract_financial_statement_history(records).balance_sheets[0]
        assert period.cash == 500.0
        assert period.total_debt == 300.0
        assert period.equity == 700.0
        assert period.working_capital == 400.0
        assert period.tangible_assets == 1000.0
        assert period.intangible_assets == 200.0

    def test_cash_flow_statement_fields(self):
        records = (
            _period(
                2023, revenue=1000.0, operating_cash_flow=250.0, investing_cash_flow=-80.0,
                financing_cash_flow=-60.0, free_cash_flow=180.0, capital_expenditure=70.0,
            ),
        )
        period = extract_financial_statement_history(records).cash_flow_statements[0]
        assert period.operating_cash_flow == 250.0
        assert period.investing_cash_flow == -80.0
        assert period.financing_cash_flow == -60.0
        assert period.free_cash_flow == 180.0
        assert period.capital_expenditure == 70.0

    def test_segments_are_always_empty(self):
        records = (_period(2023, revenue=1000.0),)
        history = extract_financial_statement_history(records)
        assert history.segments.segments == ()


class TestProvenanceAndExplainability:
    """Phase 8: every period must remain traceable back to its own
    underlying source data -- currency, accounting basis (the real
    filing form, e.g. `"10-K"`), and the provider's own filing
    reference, never manufactured when not actually supplied."""

    def test_currency_is_carried_onto_every_statement(self):
        records = (_period(2023, revenue=1000.0),)
        history = extract_financial_statement_history(records)
        assert history.income_statements[0].currency == "USD"
        assert history.balance_sheets[0].currency == "USD"
        assert history.cash_flow_statements[0].currency == "USD"

    def test_accounting_basis_reflects_the_real_filing_form(self):
        records = (_period(2023, revenue=1000.0, sec_form="10-K"),)
        history = extract_financial_statement_history(records)
        assert history.income_statements[0].accounting_basis == "10-K"

    def test_accounting_basis_is_none_when_not_reported(self):
        records = (_period(2023, revenue=1000.0),)
        history = extract_financial_statement_history(records)
        assert history.income_statements[0].accounting_basis is None

    def test_source_reference_traces_back_to_the_real_filing_url(self):
        records = (_period(2023, revenue=1000.0),)
        history = extract_financial_statement_history(records)
        assert history.income_statements[0].source_reference == "https://example.test/10k"
        assert history.balance_sheets[0].source_reference == "https://example.test/10k"
        assert history.cash_flow_statements[0].source_reference == "https://example.test/10k"


class TestTrendIntelligence:
    def test_fewer_than_three_periods_is_insufficient(self):
        records = (_period(2022, revenue=1000.0), _period(2023, revenue=1100.0))
        observations = compute_trend_intelligence(extract_financial_statement_history(records))
        revenue_trend = next(o for o in observations if o.metric is FinancialTrendMetric.REVENUE_GROWTH)
        assert revenue_trend.direction is TrendDirection.INSUFFICIENT_DATA

    def test_a_clear_revenue_rise_is_detected(self):
        records = tuple(_period(2020 + i, revenue=1000.0 + i * 500.0) for i in range(4))
        observations = compute_trend_intelligence(extract_financial_statement_history(records))
        revenue_trend = next(o for o in observations if o.metric is FinancialTrendMetric.REVENUE_GROWTH)
        assert revenue_trend.direction is TrendDirection.RISING
        assert revenue_trend.periods_considered == 4

    def test_a_clear_revenue_fall_is_detected(self):
        records = tuple(_period(2020 + i, revenue=3000.0 - i * 500.0) for i in range(4))
        observations = compute_trend_intelligence(extract_financial_statement_history(records))
        revenue_trend = next(o for o in observations if o.metric is FinancialTrendMetric.REVENUE_GROWTH)
        assert revenue_trend.direction is TrendDirection.FALLING

    def test_margin_expansion_is_a_rising_margin_trend(self):
        records = tuple(
            _period(2020 + i, revenue=1000.0, gross_profit=300.0 + i * 100.0) for i in range(4)
        )
        observations = compute_trend_intelligence(extract_financial_statement_history(records))
        margin_trend = next(o for o in observations if o.metric is FinancialTrendMetric.GROSS_MARGIN)
        assert margin_trend.direction is TrendDirection.RISING

    def test_capital_intensity_matches_capex_to_revenue_by_period(self):
        records = tuple(
            _period(2020 + i, revenue=1000.0, capital_expenditure=50.0 + i * 40.0) for i in range(4)
        )
        observations = compute_trend_intelligence(extract_financial_statement_history(records))
        intensity_trend = next(o for o in observations if o.metric is FinancialTrendMetric.CAPITAL_INTENSITY)
        assert intensity_trend.periods_considered == 4
        assert intensity_trend.direction is TrendDirection.RISING

    def test_segment_evolution_is_always_insufficient_data(self):
        records = tuple(_period(2020 + i, revenue=1000.0) for i in range(4))
        observations = compute_trend_intelligence(extract_financial_statement_history(records))
        segment_trend = next(o for o in observations if o.metric is FinancialTrendMetric.SEGMENT_EVOLUTION)
        assert segment_trend.direction is TrendDirection.INSUFFICIENT_DATA


class TestCashFlowConsistency:
    def test_fewer_than_two_periods_is_insufficient(self):
        records = (_period(2023, operating_cash_flow=100.0),)
        assert compute_cash_flow_consistency(extract_financial_statement_history(records)) is ConsistencyLevel.INSUFFICIENT_DATA

    def test_all_positive_ocf_is_consistent(self):
        records = tuple(_period(2020 + i, operating_cash_flow=100.0 + i) for i in range(3))
        assert compute_cash_flow_consistency(extract_financial_statement_history(records)) is ConsistencyLevel.CONSISTENT

    def test_a_negative_year_is_inconsistent(self):
        records = (_period(2021, operating_cash_flow=100.0), _period(2022, operating_cash_flow=-20.0), _period(2023, operating_cash_flow=150.0))
        assert compute_cash_flow_consistency(extract_financial_statement_history(records)) is ConsistencyLevel.INCONSISTENT


class TestFinancialHealth:
    def test_no_data_is_insufficient_across_every_dimension(self):
        health = assess_financial_health(extract_financial_statement_history(()))
        assert health.liquidity is FinancialHealthTier.INSUFFICIENT_DATA
        assert health.solvency is SolvencyTier.INSUFFICIENT_DATA
        assert health.earnings_durability is ConsistencyLevel.INSUFFICIENT_DATA

    def test_strong_liquidity(self):
        records = (_period(2023, current_assets=400.0, current_liabilities=100.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.liquidity is FinancialHealthTier.STRONG

    def test_weak_liquidity(self):
        records = (_period(2023, current_assets=80.0, current_liabilities=100.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.liquidity is FinancialHealthTier.WEAK

    def test_conservative_solvency(self):
        records = (_period(2023, total_debt=100.0, equity=1000.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.solvency is SolvencyTier.CONSERVATIVE

    def test_leveraged_solvency(self):
        records = (_period(2023, total_debt=2000.0, equity=1000.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.solvency is SolvencyTier.LEVERAGED

    def test_negative_profitability(self):
        records = (_period(2023, revenue=1000.0, net_income=-50.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.profitability is FinancialHealthTier.NEGATIVE

    def test_strong_profitability(self):
        records = (_period(2023, revenue=1000.0, net_income=200.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.profitability is FinancialHealthTier.STRONG

    def test_strong_cash_generation(self):
        records = (_period(2023, net_income=100.0, operating_cash_flow=150.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.cash_generation is FinancialHealthTier.STRONG

    def test_negative_cash_generation_when_net_income_non_positive(self):
        records = (_period(2023, net_income=-50.0, operating_cash_flow=10.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.cash_generation is FinancialHealthTier.NEGATIVE

    def test_well_capitalized_balance_sheet(self):
        records = (_period(2023, equity=800.0, total_assets=1000.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.balance_sheet_strength is FinancialHealthTier.STRONG

    def test_earnings_durability_consistent(self):
        records = tuple(_period(2020 + i, net_income=100.0 + i) for i in range(3))
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.earnings_durability is ConsistencyLevel.CONSISTENT

    def test_earnings_durability_inconsistent(self):
        records = (_period(2021, net_income=100.0), _period(2022, net_income=-10.0), _period(2023, net_income=50.0))
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.earnings_durability is ConsistencyLevel.INCONSISTENT

    def test_zero_debt_is_maximal_financial_flexibility(self):
        records = (_period(2023, cash=500.0, total_debt=0.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.financial_flexibility is FinancialHealthTier.STRONG

    def test_cash_exceeding_debt_is_strong_flexibility(self):
        records = (_period(2023, cash=500.0, total_debt=400.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.financial_flexibility is FinancialHealthTier.STRONG

    def test_low_cash_relative_to_debt_is_weak_flexibility(self):
        records = (_period(2023, cash=50.0, total_debt=1000.0),)
        health = assess_financial_health(extract_financial_statement_history(records))
        assert health.financial_flexibility is FinancialHealthTier.WEAK
