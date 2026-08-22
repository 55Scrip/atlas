"""Tests for `atlas.alpha.investment_case.historical_valuation`
(Capability Expansion Sprint 1, Phases 1 + 3).

Reuses `cash_flow.py`'s own test fixtures (`fcf`/`price`/`shares`/
`_market`) directly -- both the realistic multi-year timeline
construction and, in `TestConsistencyWithDecisionLayer`, as a ground-
truth oracle: this module's own `position_in_range`/`current_value`
must agree with `evaluate_fcf_yield_relative`'s own `ValuationStatus`/
`current_yield` for the *identical* inputs, since both are meant to
describe the same underlying reality.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.historical_valuation import (
    ValuationDataQuality,
    ValuationMetricKind,
    ValuationRangePosition,
    ValuationStability,
    ValuationTrend,
    extract_historical_valuation,
)
from atlas.analysis_engine.valuation.cash_flow import evaluate_fcf_yield_relative
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from tests.unit.analysis_engine.valuation.test_cash_flow import _market, fcf, price, shares
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


FY2022_PERIOD, FY2022_FILED = "2022-12-31", _dt(2023, 2, 15)
FY2023_PERIOD, FY2023_FILED = "2023-12-31", _dt(2024, 2, 15)
FY2024_PERIOD, FY2024_FILED = "2024-12-31", _dt(2025, 2, 15)
OBS_2023, OBS_2024, OBS_2025 = "2023-03-01", "2024-03-01", "2025-03-01"


class TestEmptyInput:
    def test_no_facts_at_all_produces_no_metrics(self):
        knowledge = extract_historical_valuation((), ())
        assert knowledge.metrics == ()


class TestSingleObservation:
    def test_one_valid_observation_has_a_current_value_but_no_history(self):
        business_facts = (fcf(100.0, FY2024_PERIOD, FY2024_FILED),)
        valuation_facts = _market(OBS_2025, 50.0, 100.0)
        knowledge = extract_historical_valuation(business_facts, valuation_facts)
        assert len(knowledge.metrics) == 1
        metric = knowledge.metrics[0]
        assert metric.metric is ValuationMetricKind.FCF_YIELD
        assert metric.current_value == 100.0 / (50.0 * 100.0)
        assert metric.historical_average is None
        assert metric.historical_minimum is None
        assert metric.current_percentile is None
        assert metric.position_in_range is ValuationRangePosition.INSUFFICIENT_DATA
        assert metric.trend is ValuationTrend.INSUFFICIENT_DATA
        assert metric.stability is ValuationStability.INSUFFICIENT_DATA
        assert metric.data_quality is ValuationDataQuality.INSUFFICIENT
        assert metric.coverage_period_start == metric.coverage_period_end == date(2025, 3, 1)


class TestConsistencyWithDecisionLayer:
    """The load-bearing guarantee: whatever `cash_flow.py`'s own
    evaluator concludes, this module's own statistics must agree --
    verified against the real, unmodified, public
    `evaluate_fcf_yield_relative` function (never its private helpers)
    for the identical fixtures its own test suite uses."""

    def test_undervalued_scenario_is_at_or_above_historical_high(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(110.0, FY2023_PERIOD, FY2023_FILED),
            fcf(200.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (
            *_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 52.0, 100.0), *_market(OBS_2025, 53.0, 100.0),
        )
        finding = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert finding.status is ValuationStatus.UNDERVALUED

        knowledge = extract_historical_valuation(business_facts, valuation_facts)
        metric = knowledge.metrics[0]
        assert metric.current_value == finding.current_yield
        assert metric.position_in_range is ValuationRangePosition.AT_OR_ABOVE_HISTORICAL_HIGH

    def test_fairly_valued_scenario_is_within_historical_average_band(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(105.0, FY2023_PERIOD, FY2023_FILED),
            fcf(102.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (
            *_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 50.0, 100.0), *_market(OBS_2025, 50.5, 100.0),
        )
        finding = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert finding.status is ValuationStatus.FAIRLY_VALUED

        knowledge = extract_historical_valuation(business_facts, valuation_facts)
        metric = knowledge.metrics[0]
        assert metric.current_value == finding.current_yield
        assert metric.position_in_range in (
            ValuationRangePosition.BELOW_HISTORICAL_AVERAGE,
            ValuationRangePosition.AT_HISTORICAL_AVERAGE,
            ValuationRangePosition.ABOVE_HISTORICAL_AVERAGE,
        )

    def test_expensive_scenario_is_at_or_below_historical_low(self):
        business_facts = (
            fcf(200.0, FY2022_PERIOD, FY2022_FILED),
            fcf(150.0, FY2023_PERIOD, FY2023_FILED),
            fcf(100.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (
            *_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 50.0, 100.0), *_market(OBS_2025, 50.0, 100.0),
        )
        finding = evaluate_fcf_yield_relative(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert finding.status is ValuationStatus.EXPENSIVE

        knowledge = extract_historical_valuation(business_facts, valuation_facts)
        metric = knowledge.metrics[0]
        assert metric.current_value == finding.current_yield
        assert metric.position_in_range is ValuationRangePosition.AT_OR_BELOW_HISTORICAL_LOW

    def test_historical_average_excludes_the_current_observation(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED),
            fcf(110.0, FY2023_PERIOD, FY2023_FILED),
            fcf(200.0, FY2024_PERIOD, FY2024_FILED),
        )
        valuation_facts = (
            *_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 52.0, 100.0), *_market(OBS_2025, 53.0, 100.0),
        )
        knowledge = extract_historical_valuation(business_facts, valuation_facts)
        metric = knowledge.metrics[0]
        yield_2023 = 100.0 / (50.0 * 100.0)
        yield_2024 = 110.0 / (52.0 * 100.0)
        assert metric.historical_average == (yield_2023 + yield_2024) / 2
        assert metric.historical_minimum == min(yield_2023, yield_2024)
        assert metric.historical_maximum == max(yield_2023, yield_2024)


class TestTrend:
    def _observations(self, values: tuple[float, ...]) -> tuple[tuple, tuple]:
        years = list(range(2020, 2020 + len(values)))
        business_facts = tuple(
            fcf(values[i], f"{years[i]}-12-31", _dt(years[i] + 1, 2, 15)) for i in range(len(values))
        )
        valuation_facts = tuple(
            fact for i in range(len(values)) for fact in _market(f"{years[i] + 1}-03-01", 50.0, 100.0)
        )
        return business_facts, valuation_facts

    def test_fewer_than_four_observations_is_insufficient(self):
        business_facts, valuation_facts = self._observations((100.0, 110.0, 120.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.trend is ValuationTrend.INSUFFICIENT_DATA

    def test_a_clear_rise_across_the_series_is_rising(self):
        business_facts, valuation_facts = self._observations((50.0, 60.0, 150.0, 200.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.trend is ValuationTrend.RISING

    def test_a_clear_fall_across_the_series_is_falling(self):
        business_facts, valuation_facts = self._observations((200.0, 150.0, 60.0, 50.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.trend is ValuationTrend.FALLING

    def test_a_flat_series_is_stable(self):
        business_facts, valuation_facts = self._observations((100.0, 100.0, 100.0, 100.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.trend is ValuationTrend.STABLE


class TestStability:
    def test_a_single_observation_is_insufficient(self):
        business_facts = (fcf(100.0, FY2024_PERIOD, FY2024_FILED),)
        valuation_facts = _market(OBS_2025, 50.0, 100.0)
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.stability is ValuationStability.INSUFFICIENT_DATA

    def test_near_identical_observations_are_stable(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED), fcf(101.0, FY2023_PERIOD, FY2023_FILED),
        )
        valuation_facts = (*_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 50.0, 100.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.stability is ValuationStability.STABLE

    def test_widely_swinging_observations_are_volatile(self):
        business_facts = (
            fcf(50.0, FY2022_PERIOD, FY2022_FILED), fcf(500.0, FY2023_PERIOD, FY2023_FILED),
        )
        valuation_facts = (*_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 50.0, 100.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.stability is ValuationStability.VOLATILE


class TestSignificantDeviations:
    def test_an_outlier_observation_is_flagged(self):
        business_facts = (
            fcf(100.0, "2020-12-31", _dt(2021, 2, 15)),
            fcf(105.0, "2021-12-31", _dt(2022, 2, 15)),
            fcf(98.0, "2022-12-31", _dt(2023, 2, 15)),
            fcf(2000.0, "2023-12-31", _dt(2024, 2, 15)),
        )
        valuation_facts = (
            *_market("2021-03-01", 50.0, 100.0), *_market("2022-03-01", 50.0, 100.0),
            *_market("2023-03-01", 50.0, 100.0), *_market("2024-03-01", 50.0, 100.0),
        )
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert len(metric.significant_deviations) >= 1
        assert metric.significant_deviations[-1].period_end == date(2024, 3, 1)

    def test_a_tight_series_has_no_deviations(self):
        business_facts = tuple(fcf(100.0 + i, f"{2020+i}-12-31", _dt(2021 + i, 2, 15)) for i in range(3))
        valuation_facts = tuple(
            fact for i in range(3) for fact in _market(f"{2021+i}-03-01", 50.0, 100.0)
        )
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.significant_deviations == ()


class TestMissingPeriods:
    def test_a_market_observation_with_no_eligible_fcf_is_a_missing_period(self):
        business_facts = (fcf(100.0, FY2024_PERIOD, FY2024_FILED),)
        valuation_facts = (*_market(OBS_2023, 50.0, 100.0), *_market(OBS_2025, 52.0, 100.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert date(2023, 3, 1) in metric.missing_periods
        assert date(2025, 3, 1) not in metric.missing_periods

    def test_a_non_positive_fcf_observation_is_a_missing_period(self):
        business_facts = (fcf(-10.0, FY2024_PERIOD, FY2024_FILED),)
        valuation_facts = _market(OBS_2025, 50.0, 100.0)
        knowledge = extract_historical_valuation(business_facts, valuation_facts)
        assert knowledge.metrics == ()  # zero valid observations at all


class TestDataQuality:
    def test_six_or_more_observations_is_sufficient(self):
        business_facts = tuple(fcf(100.0 + i, f"{2018+i}-12-31", _dt(2019 + i, 2, 15)) for i in range(6))
        valuation_facts = tuple(
            fact for i in range(6) for fact in _market(f"{2019+i}-03-01", 50.0, 100.0)
        )
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.data_quality is ValuationDataQuality.SUFFICIENT

    def test_two_to_five_observations_is_limited(self):
        business_facts = (
            fcf(100.0, FY2022_PERIOD, FY2022_FILED), fcf(105.0, FY2023_PERIOD, FY2023_FILED),
        )
        valuation_facts = (*_market(OBS_2023, 50.0, 100.0), *_market(OBS_2024, 50.0, 100.0))
        metric = extract_historical_valuation(business_facts, valuation_facts).metrics[0]
        assert metric.data_quality is ValuationDataQuality.LIMITED
