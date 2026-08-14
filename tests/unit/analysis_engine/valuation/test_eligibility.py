"""Tests for `atlas.analysis_engine.valuation.eligibility` (`DE-015` §9's
valuation-native eligibility rule).

Real records through `extract_facts_from_records`, matching the
established "reuse, never re-derive" fixture pattern already used
throughout `test_pipeline.py`/`test_outlook.py`.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.valuation.eligibility import (
    IneligibilityReason,
    evaluate_scenario_eligibility,
)
from tests.unit.analysis_engine.valuation._fixtures import fundamentals_record

_GENERATED_AT = datetime(2026, 8, 13, tzinfo=timezone.utc)


def _filed(year: int, month: int = 2, day: int = 15) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _durable_growth_records():
    """Real Revenue + Free Cash Flow across 6 periods, both growing
    every period -- 6 periods with a 4-year rolling window gives 2 real
    overlapping observations, the minimum a range needs to exist at
    all -- eligible on all three conditions."""
    revenue = (900.0, 1000.0, 1100.0, 1250.0, 1400.0, 1600.0)
    fcf = (90.0, 100.0, 115.0, 140.0, 165.0, 200.0)
    years = (2019, 2020, 2021, 2022, 2023, 2024)
    return tuple(
        fundamentals_record(
            period_end=date(year, 12, 31),
            identifier=f"dg{year}",
            published_at=_filed(year + 1),
            revenue=revenue[i],
            free_cash_flow=fcf[i],
        )
        for i, year in enumerate(years)
    )


def _monotonically_declining_records():
    """Both Revenue and Free Cash Flow contract every single period on
    record -- growth.py's own WEAK case, recomputed here from raw facts."""
    revenue = (1600.0, 1400.0, 1250.0, 1100.0, 1000.0)
    fcf = (200.0, 165.0, 140.0, 115.0, 100.0)
    years = (2020, 2021, 2022, 2023, 2024)
    return tuple(
        fundamentals_record(
            period_end=date(year, 12, 31),
            identifier=f"decl{year}",
            published_at=_filed(year + 1),
            revenue=revenue[i],
            free_cash_flow=fcf[i],
        )
        for i, year in enumerate(years)
    )


def _thin_history_records():
    """Only 2 periods -- not enough for even one 4-year rolling window."""
    return (
        fundamentals_record(
            period_end=date(2023, 12, 31), identifier="th23", published_at=_filed(2024), revenue=1000.0, free_cash_flow=100.0
        ),
        fundamentals_record(
            period_end=date(2024, 12, 31), identifier="th24", published_at=_filed(2025), revenue=1100.0, free_cash_flow=115.0
        ),
    )


def _fcf_only_no_revenue_corroboration_records():
    """5 periods of Free Cash Flow, growing, but Revenue is never
    reported at all -- corroboration structurally fails."""
    fcf = (100.0, 115.0, 140.0, 165.0, 200.0)
    years = (2020, 2021, 2022, 2023, 2024)
    return tuple(
        fundamentals_record(
            period_end=date(year, 12, 31), identifier=f"fo{year}", published_at=_filed(year + 1), free_cash_flow=fcf[i]
        )
        for i, year in enumerate(years)
    )


def _mixed_but_not_weak_records():
    """Revenue grows every period (STRONG_METRIC); Free Cash Flow is
    mixed (neither monotonic growth nor monotonic decline). Growth.py's
    own rule: not every supported metric is WEAK_METRIC (Revenue isn't)
    -> not the WEAK case, so condition 3 must not refuse this."""
    revenue = (1000.0, 1100.0, 1250.0, 1400.0, 1600.0)
    fcf = (100.0, 90.0, 140.0, 120.0, 200.0)
    years = (2020, 2021, 2022, 2023, 2024)
    return tuple(
        fundamentals_record(
            period_end=date(year, 12, 31),
            identifier=f"mx{year}",
            published_at=_filed(year + 1),
            revenue=revenue[i],
            free_cash_flow=fcf[i],
        )
        for i, year in enumerate(years)
    )


class TestEligibleCase:
    def test_durable_growth_is_eligible(self):
        facts = extract_facts_from_records(_durable_growth_records(), evaluated_at=_GENERATED_AT)
        result = evaluate_scenario_eligibility(facts, generated_at=_GENERATED_AT)
        assert result.eligible is True
        assert result.ineligibility_reason is None
        assert len(result.corroborated_growth_observations) >= 2

    def test_mixed_fcf_with_strong_revenue_is_eligible(self):
        """Confirms condition 3 mirrors growth.py's own rule precisely:
        one supported metric being WEAK_METRIC alone does not refuse
        eligibility -- only when *every* supported metric is."""
        facts = extract_facts_from_records(_mixed_but_not_weak_records(), evaluated_at=_GENERATED_AT)
        result = evaluate_scenario_eligibility(facts, generated_at=_GENERATED_AT)
        assert result.ineligibility_reason is not IneligibilityReason.NO_LEGITIMATE_GROWTH_BASIS


class TestNoLegitimateGrowthBasis:
    def test_monotonic_decline_on_both_metrics_is_ineligible(self):
        facts = extract_facts_from_records(_monotonically_declining_records(), evaluated_at=_GENERATED_AT)
        result = evaluate_scenario_eligibility(facts, generated_at=_GENERATED_AT)
        assert result.eligible is False
        assert result.ineligibility_reason is IneligibilityReason.NO_LEGITIMATE_GROWTH_BASIS

    def test_no_business_category_status_import_needed(self):
        """Structural confirmation: this module never imports
        BusinessCategoryStatus, BusinessFinding, or evaluate_growth --
        checked against the module's own real namespace (what it
        actually imported), not its docstring prose, which legitimately
        names these types while explaining why they are avoided."""
        import atlas.analysis_engine.valuation.eligibility as module

        for forbidden in ("BusinessCategoryStatus", "BusinessFinding", "evaluate_growth"):
            assert not hasattr(module, forbidden)


class TestInsufficientObservations:
    def test_thin_history_is_ineligible(self):
        facts = extract_facts_from_records(_thin_history_records(), evaluated_at=_GENERATED_AT)
        result = evaluate_scenario_eligibility(facts, generated_at=_GENERATED_AT)
        assert result.eligible is False
        assert result.ineligibility_reason is IneligibilityReason.INSUFFICIENT_CORROBORATED_OBSERVATIONS

    def test_missing_revenue_corroboration_is_ineligible(self):
        facts = extract_facts_from_records(_fcf_only_no_revenue_corroboration_records(), evaluated_at=_GENERATED_AT)
        result = evaluate_scenario_eligibility(facts, generated_at=_GENERATED_AT)
        assert result.eligible is False
        assert result.ineligibility_reason is IneligibilityReason.INSUFFICIENT_CORROBORATED_OBSERVATIONS

    def test_no_data_at_all_is_ineligible_not_no_growth_basis(self):
        """Absence of data must never be misclassified as evidence of
        decline (DE-015's own 'missing is not negative' discipline)."""
        result = evaluate_scenario_eligibility((), generated_at=_GENERATED_AT)
        assert result.eligible is False
        assert result.ineligibility_reason is IneligibilityReason.INSUFFICIENT_CORROBORATED_OBSERVATIONS


class TestFutureDatedExclusion:
    def test_future_dated_facts_do_not_count_toward_eligibility(self):
        records = _durable_growth_records() + (
            fundamentals_record(
                period_end=date(2027, 12, 31), identifier="future", published_at=_filed(2028), revenue=9999.0, free_cash_flow=9999.0
            ),
        )
        facts = extract_facts_from_records(records, evaluated_at=_GENERATED_AT)
        with_future = evaluate_scenario_eligibility(facts, generated_at=_GENERATED_AT)
        without_future_facts = extract_facts_from_records(_durable_growth_records(), evaluated_at=_GENERATED_AT)
        without_future = evaluate_scenario_eligibility(without_future_facts, generated_at=_GENERATED_AT)
        assert with_future.corroborated_growth_observations == without_future.corroborated_growth_observations
