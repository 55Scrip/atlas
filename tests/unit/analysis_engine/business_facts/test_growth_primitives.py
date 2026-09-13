"""Tests for `atlas.analysis_engine.business_facts.growth_primitives`
(`DE-015` §17's shared, opinion-free analytical primitive layer).

Pure unit tests only -- this module is used by nothing else yet at this
point in the DE-015 implementation sprint (per its own module docstring
instruction: "Add focused unit tests before using the module anywhere").
"""
from __future__ import annotations

import random
from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.growth_primitives import (
    FISCAL_YEAR_END_TOLERANCE_DAYS,
    DistributionSummary,
    GrowthObservation,
    compound_and_reprice_return,
    corroborated_by,
    distribution_summary,
    exclude_future_dated,
    fiscal_calendar,
    fiscal_year_values,
    fiscal_years_apart,
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


def _fcf(period: str, value: float, *, source: str = "test-record") -> BusinessFact:
    fact = _fact(BusinessFactKind.FREE_CASH_FLOW, period, value)
    return replace(fact, id=f"{source}:free_cash_flow:{period}", source_record_id=source)


def _annual(values_by_period: dict[str, float]) -> list[BusinessFact]:
    return [_fcf(period, value) for period, value in values_by_period.items()]


def _windows(facts, years=4):
    return [(o.start_period, o.end_period) for o in rolling_growth_observations(facts, years=years)]


#: NVDA's persisted FCF history (FY ends: last Sunday of January): three
#: fiscal years, a ten-year gap, then five.
NVDA_FCF = {
    "2010-01-31": 410206000.0, "2011-01-30": 577907000.0, "2012-01-29": 770421000.0,
    "2022-01-30": 8132000000.0, "2023-01-29": 3808000000.0, "2024-01-28": 27021000000.0,
    "2025-01-26": 60853000000.0, "2026-01-25": 96676000000.0,
}

#: DE's persisted FCF history around its duplicated labels: the FY2016
#: 10-K labels FY2015/FY2016 as 2015-10-31/2016-10-31, later 10-Ks as
#: 2015-11-01/2016-10-30 -- with slightly restated values.
DE_FCF = {
    "2011-10-31": 1269700000.0, "2012-10-31": -151500000.0, "2013-10-31": 2095900000.0,
    "2014-10-31": 2477600000.0, "2015-10-31": 3046300000.0, "2015-11-01": 3064800000.0,
    "2016-10-30": 3125300000.0, "2016-10-31": 3119900000.0, "2017-10-29": 1601000000.0,
    "2018-10-28": 926000000.0, "2019-11-03": 2292000000.0, "2020-11-01": 6663000000.0,
}


class TestFiscalYearIdentity:
    def test_a_52_week_year_is_one_fiscal_year(self):
        assert fiscal_years_apart("2015-10-31", "2016-10-30") == 1  # 365 days, a weekend shift

    def test_a_53_week_year_is_one_fiscal_year(self):
        assert fiscal_years_apart("2018-10-28", "2019-11-03") == 1  # 371 days

    def test_a_one_day_shift_is_the_same_fiscal_year(self):
        assert fiscal_years_apart("2015-10-31", "2015-11-01") == 0

    def test_a_quarter_is_no_whole_number_of_fiscal_years(self):
        assert fiscal_years_apart("2020-12-31", "2021-03-31") is None
        assert fiscal_years_apart("2020-12-31", "2024-06-30") is None

    def test_many_52_53_week_years_stay_whole(self):
        assert fiscal_years_apart("2010-01-31", "2026-01-25") == 16
        assert fiscal_years_apart("2007-10-31", "2025-11-02") == 18

    def test_a_label_that_is_not_a_date_has_no_identity(self):
        assert fiscal_years_apart("2020", "2024") is None
        assert fiscal_year_values([_fcf("2020", 1.0), _fcf("2024-Q3", 2.0)]) == ()

    def test_tolerance_is_two_weeks(self):
        assert FISCAL_YEAR_END_TOLERANCE_DAYS == 14
        assert fiscal_years_apart("2020-12-31", "2021-01-14") == 0
        assert fiscal_years_apart("2020-12-31", "2021-01-15") is None


class TestFiscalCalendar:
    def test_the_calendar_most_years_share_wins(self):
        periods = ["2007-11-30", "2008-11-28", "2009-12-31", "2010-12-31", "2011-12-31"]
        assert fiscal_calendar(periods) == frozenset(periods[2:])

    def test_a_tie_goes_to_the_most_recent_calendar(self):
        assert fiscal_calendar(["2018-06-30", "2019-06-30", "2020-12-31", "2021-12-31"]) == frozenset(
            {"2020-12-31", "2021-12-31"}
        )

    def test_no_periods_is_no_calendar(self):
        assert fiscal_calendar([]) == frozenset()


class TestFiscalYearValues:
    def test_one_value_per_fiscal_year_oldest_first(self):
        series = fiscal_year_values(_annual({"2021-12-31": 110.0, "2020-12-31": 100.0}))
        assert [(v.period, v.value) for v in series] == [("2020-12-31", 100.0), ("2021-12-31", 110.0)]

    def test_agreeing_reports_of_one_year_are_one_observation(self):
        facts = [_fcf("2015-10-31", 5.0, source="a"), _fcf("2015-11-01", 5.0, source="b")]
        (value,) = fiscal_year_values(facts)
        assert value.period == "2015-10-31" and value.value == 5.0
        assert value.fact_ids == ("a:free_cash_flow:2015-10-31", "b:free_cash_flow:2015-11-01")

    def test_disagreeing_reports_of_one_year_are_withheld_not_averaged(self):
        facts = [_fcf("2015-10-31", 3046.3, source="a"), _fcf("2015-11-01", 3064.8, source="b"), _fcf("2016-10-30", 3100.0)]
        assert [v.period for v in fiscal_year_values(facts)] == ["2016-10-30"]

    def test_an_exact_duplicate_period_that_disagrees_is_withheld(self):
        facts = [_fcf("2020-12-31", 1.0, source="a"), _fcf("2020-12-31", 2.0, source="b")]
        assert fiscal_year_values(facts) == ()

    def test_a_chain_of_near_duplicates_has_no_single_identity(self):
        facts = [_fcf("2020-12-20", 1.0, source="a"), _fcf("2020-12-31", 1.0, source="b"), _fcf("2021-01-10", 1.0, source="c")]
        assert fiscal_year_values(facts) == ()


class TestRollingGrowthObservations:
    def test_contiguous_fy2018_to_fy2022_is_a_4_year_window(self):
        facts = _annual({f"{y}-12-31": 100.0 * 1.1 ** (y - 2018) for y in range(2018, 2023)})
        (obs,) = rolling_growth_observations(facts, years=4)
        assert (obs.start_period, obs.end_period, obs.years) == ("2018-12-31", "2022-12-31", 4)
        assert obs.rate == pytest.approx(0.1, abs=1e-12)

    def test_fy2018_to_fy2023_is_not_a_4_year_window(self):
        facts = _annual({"2018-12-31": 100.0, "2023-12-31": 200.0})
        assert rolling_growth_observations(facts, years=4) == ()
        (five,) = rolling_growth_observations(facts, years=5)
        assert five.rate == pytest.approx(2.0 ** (1 / 5) - 1)

    def test_a_shorter_span_is_not_a_4_year_window(self):
        assert rolling_growth_observations(_annual({"2019-12-31": 100.0, "2022-12-31": 200.0}), years=4) == ()

    def test_a_large_missing_year_gap_produces_no_window_across_it(self):
        facts = _annual({"2010-12-31": 1.0, "2011-12-31": 2.0, "2020-12-31": 50.0, "2021-12-31": 60.0})
        assert rolling_growth_observations(facts, years=4) == ()

    def test_a_missing_endpoint_year_gives_no_window_not_the_nearest(self):
        facts = _annual({"2018-12-31": 100.0, "2019-12-31": 110.0, "2021-12-31": 130.0, "2023-12-31": 150.0})
        assert _windows(facts) == [("2019-12-31", "2023-12-31")]

    def test_nvda_shaped_history_has_one_4_year_window(self):
        """List positions paired FY2010->FY2023, FY2011->FY2024 and
        FY2012->FY2025 -- 13-year spans -- and annualised them over four."""
        (obs,) = rolling_growth_observations(_annual(NVDA_FCF), years=4)
        assert (obs.start_period, obs.end_period) == ("2022-01-30", "2026-01-25")
        assert obs.rate == pytest.approx((96676000000.0 / 8132000000.0) ** 0.25 - 1)

    def test_52_and_53_week_years_form_windows(self):
        facts = _annual({"2014-10-31": 1.0, "2015-11-01": 1.1, "2016-10-30": 1.2, "2017-10-29": 1.3, "2018-10-28": 1.4, "2019-11-03": 1.5})
        assert _windows(facts) == [("2014-10-31", "2018-10-28"), ("2015-11-01", "2019-11-03")]

    def test_de_shaped_duplicates_manufacture_no_extra_years_or_windows(self):
        """Old: 2013->2016-10-30 (3y), 2014->2016-10-31 (2y), 2015-10-31
        ->2017 (2y), 2015-11-01->2018 (3y) all passed as 4-year windows."""
        windows = rolling_growth_observations(_annual(DE_FCF), years=4)
        assert [(o.start_period, o.end_period) for o in windows] == [
            ("2013-10-31", "2017-10-29"), ("2014-10-31", "2018-10-28"),
        ]
        assert all(fiscal_years_apart(o.start_period, o.end_period) == 4 for o in windows)

    def test_agreeing_duplicates_count_once(self):
        facts = _annual({f"{y}-12-31": 100.0 + y - 2018 for y in range(2018, 2023)}) + [_fcf("2023-01-01", 104.0, source="dup")]
        assert len(rolling_growth_observations(facts, years=4)) == 1

    def test_shuffled_input_gives_identical_windows(self):
        facts = _annual(DE_FCF)
        expected = rolling_growth_observations(facts, years=4)
        for seed in range(5):
            shuffled = facts[:]
            random.Random(seed).shuffle(shuffled)
            assert rolling_growth_observations(shuffled, years=4) == expected

    def test_zero_starting_value_forms_no_window(self):
        assert rolling_growth_observations(_annual({"2020-12-31": 0.0, "2024-12-31": 100.0}), years=4) == ()

    def test_negative_starting_value_forms_no_window(self):
        assert rolling_growth_observations(_annual({"2020-12-31": -50.0, "2024-12-31": 100.0}), years=4) == ()

    def test_negative_ending_value_forms_no_window(self):
        assert rolling_growth_observations(_annual({"2020-12-31": 50.0, "2024-12-31": -100.0}), years=4) == ()

    def test_a_quarterly_fact_in_annual_history_is_never_an_endpoint(self):
        annual = _annual({f"{y}-12-31": 100.0 + y for y in range(2018, 2023)})
        with_quarter = annual + [_fcf("2020-06-30", 7.0, source="q"), _fcf("2024-06-30", 9.0, source="q2")]
        assert _windows(with_quarter) == _windows(annual) == [("2018-12-31", "2022-12-31")]

    def test_every_window_is_exactly_its_stated_number_of_fiscal_years(self):
        for facts in (_annual(NVDA_FCF), _annual(DE_FCF)):
            for years in (1, 2, 3, 4, 5):
                for obs in rolling_growth_observations(facts, years=years):
                    assert obs.years == years
                    assert fiscal_years_apart(obs.start_period, obs.end_period) == years
                    assert obs.start_period < obs.end_period
                    assert obs.rate == pytest.approx((obs.end_value / obs.start_value) ** (1 / years) - 1)

    def test_provenance_names_the_endpoint_facts(self):
        (obs,) = rolling_growth_observations(_annual({"2020-12-31": 100.0, "2024-12-31": 200.0}), years=4)
        assert obs.source_fact_ids == ("test-record:free_cash_flow:2020-12-31", "test-record:free_cash_flow:2024-12-31")
        assert (obs.start_value, obs.end_value) == (100.0, 200.0)

    def test_too_few_periods_yields_no_observations(self):
        assert rolling_growth_observations(_annual({"2022-12-31": 100.0}), years=4) == ()


def _observation(start: str, end: str) -> GrowthObservation:
    return GrowthObservation(start, end, 0.1, years=4, start_value=1.0, end_value=1.5, source_fact_ids=())


class TestCorroboratedBy:
    def test_keeps_only_observations_with_both_endpoints_present(self):
        observations = (_observation("2020-12-31", "2024-12-31"), _observation("2021-12-31", "2025-12-31"))
        periods = frozenset({"2020-12-31", "2024-12-31"})
        assert corroborated_by(observations, periods) == (observations[0],)

    def test_exact_membership_not_bounds_check(self):
        """A window whose endpoints straddle a real corroborating gap
        must NOT be treated as corroborated merely because both
        endpoints fall within the min/max of the corroborating set --
        only real presence at both endpoint years counts."""
        observations = (_observation("2011-12-31", "2015-12-31"),)
        periods = frozenset({"2010-12-31", "2016-12-31"})
        assert corroborated_by(observations, periods) == ()

    def test_a_report_of_the_same_fiscal_year_corroborates(self):
        observations = (_observation("2015-10-31", "2019-11-03"),)
        assert corroborated_by(observations, frozenset({"2015-11-01", "2019-11-03"})) == observations

    def test_empty_corroborating_set_corroborates_nothing(self):
        assert corroborated_by((_observation("2020-12-31", "2024-12-31"),), frozenset()) == ()


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
