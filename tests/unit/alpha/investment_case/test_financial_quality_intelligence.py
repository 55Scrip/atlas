"""Tests for `atlas.alpha.investment_case.financial_quality_intelligence`
(Capability Expansion Sprint 5, Phases 1 + 3 through 8).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.financial_quality_intelligence import (
    CashFlowDirection,
    ConsistencyLevel,
    ConversionPattern,
    DurabilityFinding,
    MarginKind,
    StabilityLevel,
    TrendDirection,
    UnsupportedMeasureReason,
    extract_financial_quality,
)
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
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


def _history(records):
    return extract_financial_statement_history(records)


class TestEmptyInput:
    def test_no_data_yields_history_insufficient_across_every_dimension(self):
        quality = extract_financial_quality(_history(()))
        assert quality.cash_conversion.ocf_conversion_pattern is ConversionPattern.INSUFFICIENT_HISTORY
        assert quality.working_capital.trend is TrendDirection.INSUFFICIENT_DATA
        assert quality.profitability_durability.net_margin.trend is TrendDirection.INSUFFICIENT_DATA
        assert quality.capital_efficiency.return_on_assets_trend is TrendDirection.INSUFFICIENT_DATA
        assert quality.financial_durability.findings == (DurabilityFinding.HISTORY_INSUFFICIENT,)


class TestCashConversion:
    def test_ratios_are_computed_per_period(self):
        records = (_period(2023, net_income=100.0, operating_income=150.0, operating_cash_flow=90.0, free_cash_flow=70.0),)
        quality = extract_financial_quality(_history(records))
        obs = quality.cash_conversion.observations[0]
        assert obs.ocf_to_net_income == 0.9
        assert obs.fcf_to_net_income == 0.7
        assert obs.fcf_to_operating_income == 70.0 / 150.0

    def test_strongly_supported_pattern_when_conversion_is_high(self):
        records = tuple(_period(2020 + i, net_income=100.0, operating_cash_flow=95.0) for i in range(3))
        quality = extract_financial_quality(_history(records))
        assert quality.cash_conversion.ocf_conversion_pattern is ConversionPattern.STRONGLY_SUPPORTED

    def test_persistently_divergent_pattern_when_conversion_is_low(self):
        records = tuple(_period(2020 + i, net_income=100.0, operating_cash_flow=20.0) for i in range(3))
        quality = extract_financial_quality(_history(records))
        assert quality.cash_conversion.ocf_conversion_pattern is ConversionPattern.PERSISTENTLY_DIVERGENT

    def test_insufficient_history_with_fewer_than_two_periods(self):
        records = (_period(2023, net_income=100.0, operating_cash_flow=95.0),)
        quality = extract_financial_quality(_history(records))
        assert quality.cash_conversion.ocf_conversion_pattern is ConversionPattern.INSUFFICIENT_HISTORY

    def test_improving_conversion_trend_is_detected(self):
        records = tuple(_period(2020 + i, net_income=100.0, operating_cash_flow=20.0 + i * 25.0) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert quality.cash_conversion.ocf_conversion_trend is TrendDirection.RISING


class TestWorkingCapital:
    def test_cash_absorbed_when_working_capital_increases(self):
        # `working_capital` is provider-derived (`sec_edgar.py`'s own
        # `current_assets - current_liabilities`), not re-derived by
        # `financial_statement_intelligence.py` -- set explicitly here
        # since this fixture bypasses the real provider.
        records = (
            _period(2022, current_assets=300.0, current_liabilities=100.0, working_capital=200.0),
            _period(2023, current_assets=400.0, current_liabilities=100.0, working_capital=300.0),
        )
        quality = extract_financial_quality(_history(records))
        assert quality.working_capital.most_recent_direction is CashFlowDirection.CASH_ABSORBED

    def test_cash_released_when_working_capital_decreases(self):
        records = (
            _period(2022, current_assets=400.0, current_liabilities=100.0, working_capital=300.0),
            _period(2023, current_assets=300.0, current_liabilities=100.0, working_capital=200.0),
        )
        quality = extract_financial_quality(_history(records))
        assert quality.working_capital.most_recent_direction is CashFlowDirection.CASH_RELEASED

    def test_working_capital_to_revenue_ratio(self):
        records = (_period(2023, revenue=1000.0, current_assets=300.0, current_liabilities=100.0, working_capital=200.0),)
        quality = extract_financial_quality(_history(records))
        assert quality.working_capital.observations[0].working_capital_to_revenue == 0.2


class TestProfitabilityDurability:
    def test_current_level_is_the_most_recent_margin(self):
        records = (_period(2023, revenue=1000.0, net_income=150.0),)
        quality = extract_financial_quality(_history(records))
        assert quality.profitability_durability.net_margin.current_level == 0.15

    def test_stable_margins_are_classified_stable(self):
        records = tuple(_period(2020 + i, revenue=1000.0, net_income=150.0 + i) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert quality.profitability_durability.net_margin.stability is StabilityLevel.STABLE

    def test_volatile_margins_are_classified_volatile(self):
        records = (
            _period(2020, revenue=1000.0, net_income=150.0),
            _period(2021, revenue=1000.0, net_income=10.0),
            _period(2022, revenue=1000.0, net_income=400.0),
            _period(2023, revenue=1000.0, net_income=50.0),
        )
        quality = extract_financial_quality(_history(records))
        assert quality.profitability_durability.net_margin.stability is StabilityLevel.VOLATILE

    def test_a_large_reversal_is_flagged(self):
        records = (
            _period(2020, revenue=1000.0, net_income=150.0),
            _period(2021, revenue=1000.0, net_income=155.0),
            _period(2022, revenue=1000.0, net_income=145.0),
            _period(2023, revenue=1000.0, net_income=900.0),
        )
        quality = extract_financial_quality(_history(records))
        assert len(quality.profitability_durability.net_margin.reversals) >= 1
        assert quality.profitability_durability.net_margin.reversals[-1].period_end == date(2023, 12, 31)

    def test_margin_trend_matches_financial_statement_intelligence(self):
        records = tuple(_period(2020 + i, revenue=1000.0, gross_profit=300.0 + i * 100.0) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert quality.profitability_durability.gross_margin.trend is TrendDirection.RISING


class TestCapitalEfficiency:
    def test_return_on_assets_and_equity_are_computed(self):
        records = (_period(2023, net_income=100.0, total_assets=1000.0, equity=500.0, revenue=800.0),)
        quality = extract_financial_quality(_history(records))
        obs = quality.capital_efficiency.observations[0]
        assert obs.return_on_assets == 0.1
        assert obs.return_on_equity == 0.2
        assert obs.asset_turnover == 0.8

    def test_roic_is_always_explicitly_unavailable(self):
        records = (_period(2023, net_income=100.0, total_assets=1000.0),)
        quality = extract_financial_quality(_history(records))
        assert (
            quality.capital_efficiency.return_on_invested_capital_unavailable_reason
            is UnsupportedMeasureReason.MISSING_TAX_RATE_INPUT
        )

    def test_rising_return_on_assets_is_detected(self):
        records = tuple(_period(2020 + i, net_income=50.0 + i * 30.0, total_assets=1000.0) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert quality.capital_efficiency.return_on_assets_trend is TrendDirection.RISING


class TestFinancialDurability:
    def test_consistently_positive_cash_generation_is_reused_from_financial_statement_intelligence(self):
        records = tuple(_period(2020 + i, operating_cash_flow=50.0 + i) for i in range(3))
        quality = extract_financial_quality(_history(records))
        assert DurabilityFinding.CASH_GENERATION_CONSISTENTLY_POSITIVE in quality.financial_durability.findings

    def test_inconsistent_cash_generation_is_flagged(self):
        records = (
            _period(2021, operating_cash_flow=50.0), _period(2022, operating_cash_flow=-20.0),
            _period(2023, operating_cash_flow=60.0),
        )
        quality = extract_financial_quality(_history(records))
        assert DurabilityFinding.CASH_GENERATION_INCONSISTENT in quality.financial_durability.findings

    def test_stable_profitability_is_flagged(self):
        records = tuple(_period(2020 + i, revenue=1000.0, net_income=150.0 + i) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert DurabilityFinding.PROFITABILITY_HIGHLY_STABLE in quality.financial_durability.findings

    def test_improving_cash_conversion_is_flagged(self):
        records = tuple(_period(2020 + i, net_income=100.0, operating_cash_flow=20.0 + i * 25.0) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert DurabilityFinding.CASH_CONVERSION_IMPROVING in quality.financial_durability.findings

    def test_strengthening_capital_efficiency_is_flagged(self):
        records = tuple(_period(2020 + i, net_income=50.0 + i * 30.0, total_assets=1000.0) for i in range(4))
        quality = extract_financial_quality(_history(records))
        assert DurabilityFinding.CAPITAL_EFFICIENCY_STRENGTHENING in quality.financial_durability.findings
