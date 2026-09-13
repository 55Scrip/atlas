"""Tests for `atlas.alpha.investment_case.historical_valuation`
(Capability Expansion Sprint 1; Valuation Observation Integrity).

The time series is the FCF-yield finding's own fiscal epochs -- the prior
fiscal years, then today's observation -- never a second construction.
`TestOneConstruction` pins that: whatever the evaluator compared, this
module describes exactly that, value for value.
"""
from __future__ import annotations

from datetime import date

from atlas.alpha.investment_case.historical_valuation import (
    ValuationDataQuality,
    ValuationMetricKind,
    ValuationRangePosition,
    ValuationStability,
    ValuationTrend,
    extract_historical_valuation,
)
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from tests.unit.analysis_engine.valuation._epochs import (
    annual_history,
    evaluate,
    filed_on,
    first_quote_day,
    quote,
    statement_fcf,
)


def knowledge(business, market, **kwargs):
    finding = evaluate(business, market, **kwargs)
    return finding, extract_historical_valuation(finding, tuple(market))


def series(fcf_values, today_price=50.0, price=50.0):
    """One fiscal year per value (from 2018), the first observation after
    each filing but the last, and today's price against the last year."""
    years = list(range(2018, 2018 + len(fcf_values)))
    business, market = annual_history(dict(zip(years, fcf_values)), {y: price for y in years[:-1]})
    return business, [*market, *quote("2026-08-20", today_price)]


class TestEmptyInput:
    def test_no_facts_at_all_produces_no_metrics(self):
        assert knowledge((), ())[1].metrics == ()

    def test_a_method_that_does_not_apply_produces_no_metrics(self):
        _, result = knowledge(*series((100.0, 110.0, 120.0, 130.0)), industry="BANKS - DIVERSIFIED")
        assert result.metrics == ()


class TestSingleObservation:
    def test_one_fiscal_year_has_a_current_value_but_no_history(self):
        business, market = annual_history({2024: 100.0}, {})
        finding, result = knowledge(business, [*market, *quote("2026-08-20", 50.0)])
        metric = result.metrics[0]
        assert metric.metric is ValuationMetricKind.FCF_YIELD
        assert metric.current_value == finding.current_yield == 100.0 / (50.0 * 100.0)
        assert metric.historical_average is None and metric.historical_minimum is None
        assert metric.current_percentile is None
        assert metric.position_in_range is ValuationRangePosition.INSUFFICIENT_DATA
        assert metric.trend is ValuationTrend.INSUFFICIENT_DATA
        assert metric.stability is ValuationStability.INSUFFICIENT_DATA
        assert metric.data_quality is ValuationDataQuality.INSUFFICIENT
        assert metric.coverage_period_start == metric.coverage_period_end == date(2026, 8, 20)


class TestOneConstruction:
    """The load-bearing guarantee: the observations here are the
    evaluator's own epochs, so its classification and this description can
    never disagree."""

    def test_observations_are_the_prior_epochs_then_the_current_one(self):
        finding, result = knowledge(*series((100.0, 110.0, 120.0, 200.0), today_price=53.0))
        evidence = finding.fcf_yield_evidence
        expected = [*(e.fcf_yield for e in evidence.prior_epochs), evidence.current.fcf_yield]
        assert [o.value for o in result.metrics[0].observations] == expected

    def test_undervalued_is_at_or_above_the_historical_high(self):
        finding, result = knowledge(*series((100.0, 110.0, 120.0, 200.0), today_price=53.0))
        assert finding.status is ValuationStatus.UNDERVALUED
        assert result.metrics[0].position_in_range is ValuationRangePosition.AT_OR_ABOVE_HISTORICAL_HIGH

    def test_fairly_valued_is_within_the_historical_band(self):
        finding, result = knowledge(*series((100.0, 105.0, 110.0, 104.0), today_price=50.0))
        assert finding.status is ValuationStatus.FAIRLY_VALUED
        assert result.metrics[0].position_in_range in (
            ValuationRangePosition.BELOW_HISTORICAL_AVERAGE,
            ValuationRangePosition.AT_HISTORICAL_AVERAGE,
            ValuationRangePosition.ABOVE_HISTORICAL_AVERAGE,
        )

    def test_expensive_is_at_or_below_the_historical_low(self):
        finding, result = knowledge(*series((200.0, 150.0, 120.0, 100.0), today_price=50.0))
        assert finding.status is ValuationStatus.EXPENSIVE
        assert result.metrics[0].position_in_range is ValuationRangePosition.AT_OR_BELOW_HISTORICAL_LOW

    def test_historical_statistics_exclude_the_current_observation(self):
        finding, result = knowledge(*series((100.0, 110.0, 120.0, 200.0), today_price=53.0))
        prior = finding.fcf_yield_evidence.prior_yields
        metric = result.metrics[0]
        assert metric.historical_average == sum(prior) / len(prior)
        assert (metric.historical_minimum, metric.historical_maximum) == (min(prior), max(prior))

    def test_refreshes_of_one_fiscal_year_are_neither_observations_nor_gaps(self):
        business, market = series((100.0, 110.0, 120.0, 130.0))
        refreshed = [*market, *quote("2026-08-07", 49.0), *quote("2025-11-28", 48.0)]
        _, result = knowledge(business, refreshed)
        metric = result.metrics[0]
        assert len(metric.observations) == 4
        assert date(2026, 8, 7) not in metric.missing_periods
        assert date(2025, 11, 28) not in metric.missing_periods

    def test_a_limited_history_is_still_described(self):
        finding, result = knowledge(*series((100.0, 110.0, 120.0), today_price=80.0))
        assert finding.status is ValuationStatus.INSUFFICIENT_INPUT
        assert result.metrics[0].position_in_range is ValuationRangePosition.AT_OR_BELOW_HISTORICAL_LOW
        assert result.metrics[0].data_quality is ValuationDataQuality.LIMITED


class TestTrend:
    def test_fewer_than_four_observations_is_insufficient(self):
        _, result = knowledge(*series((100.0, 110.0, 120.0)))
        assert result.metrics[0].trend is ValuationTrend.INSUFFICIENT_DATA

    def test_a_clear_rise_across_the_series_is_rising(self):
        _, result = knowledge(*series((50.0, 60.0, 150.0, 200.0)))
        assert result.metrics[0].trend is ValuationTrend.RISING

    def test_a_clear_fall_across_the_series_is_falling(self):
        _, result = knowledge(*series((200.0, 150.0, 60.0, 50.0)))
        assert result.metrics[0].trend is ValuationTrend.FALLING

    def test_a_flat_series_is_stable(self):
        _, result = knowledge(*series((100.0, 100.0, 100.0, 100.0)))
        assert result.metrics[0].trend is ValuationTrend.STABLE


class TestStability:
    def test_a_single_observation_is_insufficient(self):
        _, result = knowledge(*series((100.0,)))
        assert result.metrics[0].stability is ValuationStability.INSUFFICIENT_DATA

    def test_near_identical_observations_are_stable(self):
        _, result = knowledge(*series((100.0, 101.0)))
        assert result.metrics[0].stability is ValuationStability.STABLE

    def test_widely_swinging_observations_are_volatile(self):
        _, result = knowledge(*series((50.0, 500.0)))
        assert result.metrics[0].stability is ValuationStability.VOLATILE


class TestSignificantDeviations:
    def test_an_outlier_observation_is_flagged(self):
        _, result = knowledge(*series((100.0, 105.0, 98.0, 2000.0)))
        metric = result.metrics[0]
        assert len(metric.significant_deviations) >= 1
        assert metric.significant_deviations[-1].period_end == date(2026, 8, 20)

    def test_a_tight_series_has_no_deviations(self):
        _, result = knowledge(*series((100.0, 101.0, 102.0)))
        assert result.metrics[0].significant_deviations == ()


class TestMissingPeriods:
    def test_a_price_before_any_fiscal_year_was_public_is_a_missing_period(self):
        business = [statement_fcf(100.0, "2024-12-31", filed_on(2024))]
        market = [*quote("2024-06-28", 50.0), *quote("2026-08-20", 52.0)]
        metric = knowledge(business, market)[1].metrics[0]
        assert date(2024, 6, 28) in metric.missing_periods
        assert date(2026, 8, 20) not in metric.missing_periods

    def test_a_non_positive_fiscal_year_is_a_missing_period(self):
        business, market = annual_history({2021: 100.0, 2022: -10.0, 2023: 120.0}, {2021: 50.0, 2022: 50.0})
        metric = knowledge(business, [*market, *quote("2026-08-20", 50.0)])[1].metrics[0]
        assert date.fromisoformat(first_quote_day(2022)) in metric.missing_periods

    def test_no_current_observation_produces_no_metrics(self):
        business, market = annual_history({2023: 100.0, 2024: -10.0}, {2023: 50.0})
        _, result = knowledge(business, [*market, *quote("2026-08-20", 50.0)])
        assert result.metrics == ()


class TestDataQuality:
    def test_six_or_more_observations_is_sufficient(self):
        _, result = knowledge(*series(tuple(100.0 + i for i in range(6))))
        assert result.metrics[0].data_quality is ValuationDataQuality.SUFFICIENT

    def test_two_to_five_observations_is_limited(self):
        _, result = knowledge(*series((100.0, 105.0)))
        assert result.metrics[0].data_quality is ValuationDataQuality.LIMITED
