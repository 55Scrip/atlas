"""Tests for `atlas.analysis_engine.business_facts.growth_primitives`
(`DE-015` §17's shared, opinion-free analytical primitive layer).

Pure unit tests only -- this module is used by nothing else yet at this
point in the DE-015 implementation sprint (per its own module docstring
instruction: "Add focused unit tests before using the module anywhere").
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.growth_primitives import (
    DistributionSummary,
    GrowthObservation,
    compound_and_reprice_return,
    corroborated_by,
    distribution_summary,
    exclude_future_dated,
    real_periods,
    rolling_growth_observations,
    sorted_facts_of_kind,
)
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger

_COMPUTED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _fact(kind: BusinessFactKind, period: str, value: float, *, published_at: datetime | None = None) -> BusinessFact:
    return BusinessFact(
        id=f"test:{kind.value}:{period}",
        company="TEST",
        kind=kind,
        value=value,
        unit="USD",
        period=period,
        source_record_id="test-record",
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=(),
            computed_at=_COMPUTED_AT,
        ),
        extracted_at=_COMPUTED_AT,
        published_at=published_at if published_at is not None else _COMPUTED_AT,
    )


class TestSortedFactsOfKind:
    def test_filters_and_sorts(self):
        facts = (
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2024-12-31", 100.0),
            _fact(BusinessFactKind.REVENUE, "2023-12-31", 500.0),
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2022-12-31", 80.0),
        )
        result = sorted_facts_of_kind(facts, BusinessFactKind.FREE_CASH_FLOW)
        assert [f.period for f in result] == ["2022-12-31", "2024-12-31"]

    def test_empty_when_no_match(self):
        facts = (_fact(BusinessFactKind.REVENUE, "2023-12-31", 500.0),)
        assert sorted_facts_of_kind(facts, BusinessFactKind.FREE_CASH_FLOW) == []


class TestExcludeFutureDated:
    def test_excludes_periods_after_as_of(self):
        facts = [
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2024-12-31", 100.0),
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2027-09-26", 999.0),
        ]
        result = exclude_future_dated(facts, as_of=datetime(2026, 1, 1, tzinfo=timezone.utc))
        assert [f.period for f in result] == ["2024-12-31"]

    def test_period_exactly_on_as_of_is_kept(self):
        facts = [_fact(BusinessFactKind.FREE_CASH_FLOW, "2026-01-01", 100.0)]
        result = exclude_future_dated(facts, as_of=datetime(2026, 1, 1, tzinfo=timezone.utc))
        assert len(result) == 1


class TestRealPeriods:
    def test_returns_exact_period_set(self):
        facts = [
            _fact(BusinessFactKind.REVENUE, "2022-12-31", 100.0),
            _fact(BusinessFactKind.REVENUE, "2024-12-31", 120.0),
        ]
        assert real_periods(facts) == frozenset({"2022-12-31", "2024-12-31"})

    def test_empty_series_yields_empty_set(self):
        assert real_periods([]) == frozenset()


class TestRollingGrowthObservations:
    def test_one_window_from_four_periods_years_two(self):
        facts = [
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2020-12-31", 100.0),
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2021-12-31", 110.0),
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2022-12-31", 121.0),
        ]
        result = rolling_growth_observations(facts, years=2)
        assert len(result) == 1
        obs = result[0]
        assert obs.start_period == "2020-12-31"
        assert obs.end_period == "2022-12-31"
        assert obs.rate == pytest.approx(0.1, abs=1e-9)

    def test_multiple_overlapping_windows(self):
        facts = [
            _fact(BusinessFactKind.FREE_CASH_FLOW, str(year), 100.0 * (1.05 ** i))
            for i, year in enumerate(range(2018, 2025))
        ]
        result = rolling_growth_observations(facts, years=3)
        assert len(result) == 4  # 7 periods, window 3 -> 7-3 = 4 observations

    def test_excludes_windows_with_non_positive_endpoint(self):
        facts = [
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2020-12-31", -50.0),
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2021-12-31", 10.0),
            _fact(BusinessFactKind.FREE_CASH_FLOW, "2022-12-31", 100.0),
        ]
        result = rolling_growth_observations(facts, years=2)
        assert result == ()

    def test_too_few_periods_yields_no_observations(self):
        facts = [_fact(BusinessFactKind.FREE_CASH_FLOW, "2022-12-31", 100.0)]
        assert rolling_growth_observations(facts, years=4) == ()

    def test_returns_growth_observation_instances(self):
        facts = [
            _fact(BusinessFactKind.FREE_CASH_FLOW, str(year), 100.0 + i * 10)
            for i, year in enumerate(range(2020, 2025))
        ]
        result = rolling_growth_observations(facts, years=4)
        assert isinstance(result[0], GrowthObservation)


class TestCorroboratedBy:
    def test_keeps_only_observations_with_both_endpoints_present(self):
        observations = (
            GrowthObservation("2020-12-31", "2024-12-31", 0.1),
            GrowthObservation("2021-12-31", "2025-12-31", 0.2),
        )
        periods = frozenset({"2020-12-31", "2024-12-31"})
        result = corroborated_by(observations, periods)
        assert result == (observations[0],)

    def test_exact_membership_not_bounds_check(self):
        """A window whose endpoints straddle a real corroborating gap
        must NOT be treated as corroborated merely because both
        endpoints fall within the min/max of the corroborating set --
        only real presence at both exact periods counts."""
        observations = (GrowthObservation("2011-12-31", "2015-12-31", 0.3),)
        # Corroborating periods exist before and after the gap, but not
        # at the window's own two exact endpoints.
        periods = frozenset({"2010-12-31", "2016-12-31"})
        assert corroborated_by(observations, periods) == ()

    def test_empty_corroborating_set_corroborates_nothing(self):
        observations = (GrowthObservation("2020-12-31", "2024-12-31", 0.1),)
        assert corroborated_by(observations, frozenset()) == ()


class TestDistributionSummary:
    def test_min_median_max(self):
        result = distribution_summary((0.05, 0.10, 0.20))
        assert result == DistributionSummary(minimum=0.05, median=0.10, maximum=0.20)

    def test_single_value(self):
        result = distribution_summary((0.07,))
        assert result == DistributionSummary(minimum=0.07, median=0.07, maximum=0.07)

    def test_empty_returns_none(self):
        assert distribution_summary(()) is None

    def test_even_count_median_is_interpolated(self):
        result = distribution_summary((0.0, 0.10))
        assert result.median == pytest.approx(0.05)


class TestCompoundAndRepriceReturn:
    def test_positive_growth_positive_return(self):
        result = compound_and_reprice_return(current_value=0.05, growth_rate=0.10, years=4, terminal_value=0.05)
        assert result > 0
        assert result == pytest.approx((1.10 ** 4) ** (1 / 4) - 1.0, abs=1e-9)

    def test_zero_growth_pure_reprice(self):
        result = compound_and_reprice_return(current_value=0.05, growth_rate=0.0, years=4, terminal_value=0.10)
        # current/terminal < 1 -> reprice down -> negative return
        assert result < 0

    def test_terminal_value_varies_independently_of_growth(self):
        favorable = compound_and_reprice_return(current_value=0.05, growth_rate=0.05, years=4, terminal_value=0.03)
        unfavorable = compound_and_reprice_return(current_value=0.05, growth_rate=0.05, years=4, terminal_value=0.08)
        assert favorable > unfavorable

    def test_negative_growth_can_still_yield_positive_return_if_repriced_favorably(self):
        result = compound_and_reprice_return(current_value=0.08, growth_rate=-0.05, years=4, terminal_value=0.02)
        assert result > 0
