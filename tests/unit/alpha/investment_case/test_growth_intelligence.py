"""Tests for `atlas.alpha.investment_case.growth_intelligence`
(Capability Expansion Sprint 6, Phases 1 + 3 through 6).

Reuses `tests.unit.analysis_engine.test_growth`'s own `fact()` helper
directly, both to build realistic `BusinessFact` fixtures and, in
`TestConsistencyCrossCheck`, as the ground-truth oracle: this module's
own `GrowthDurability.consistency` for Revenue/FCF must agree with
`growth.classify_metric_trend`'s own conclusion for the identical
facts.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import (
    GrowthConsistency,
    GrowthPattern,
    RecoveryStatus,
    TrendDirection,
    extract_growth_knowledge,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.growth import MetricTrend, classify_metric_trend
from tests.unit.analysis_engine.test_growth import fact

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


def _knowledge(records):
    return extract_growth_knowledge(extract_financial_statement_history(records))


class TestEmptyInput:
    def test_no_data_yields_insufficient_data_everywhere(self):
        knowledge = _knowledge(())
        assert knowledge.revenue.direction is TrendDirection.INSUFFICIENT_DATA
        assert knowledge.revenue.durability.consistency is GrowthConsistency.INSUFFICIENT_DATA
        assert knowledge.revenue.cagr is None
        assert knowledge.segment_growth.available is False


class TestObservationsAndCagr:
    def test_year_over_year_growth_is_computed(self):
        records = (_period(2022, revenue=1000.0), _period(2023, revenue=1100.0))
        knowledge = _knowledge(records)
        obs = knowledge.revenue.observations
        assert obs[0].year_over_year_growth is None
        assert obs[1].year_over_year_growth == 0.1

    def test_cagr_over_multiple_years(self):
        records = (_period(2020, revenue=1000.0), _period(2021, revenue=1100.0), _period(2022, revenue=1210.0))
        knowledge = _knowledge(records)
        assert abs(knowledge.revenue.cagr - 0.1) < 1e-9

    def test_cagr_is_none_when_start_or_end_value_is_non_positive(self):
        records = (_period(2020, revenue=1000.0, net_income=-50.0), _period(2021, revenue=1100.0, net_income=100.0))
        knowledge = _knowledge(records)
        assert knowledge.earnings.cagr is None

    def test_cagr_is_none_with_fewer_than_two_known_periods(self):
        records = (_period(2023, revenue=1000.0),)
        knowledge = _knowledge(records)
        assert knowledge.revenue.cagr is None


class TestDirectionAndPattern:
    def test_rising_revenue_is_detected(self):
        records = tuple(_period(2020 + i, revenue=1000.0 + i * 500.0) for i in range(4))
        knowledge = _knowledge(records)
        assert knowledge.revenue.direction is TrendDirection.RISING

    def test_accelerating_growth_is_detected(self):
        # YoY growth rate itself rising over time.
        records = (
            _period(2020, revenue=1000.0), _period(2021, revenue=1050.0), _period(2022, revenue=1150.0),
            _period(2023, revenue=1400.0),
        )
        knowledge = _knowledge(records)
        assert knowledge.revenue.pattern is GrowthPattern.ACCELERATING

    def test_volatile_growth_is_detected(self):
        records = (
            _period(2020, revenue=1000.0), _period(2021, revenue=1500.0), _period(2022, revenue=1100.0),
            _period(2023, revenue=1800.0),
        )
        knowledge = _knowledge(records)
        assert knowledge.revenue.pattern is GrowthPattern.VOLATILE

    def test_insufficient_pattern_with_too_few_periods(self):
        records = (_period(2022, revenue=1000.0), _period(2023, revenue=1100.0))
        knowledge = _knowledge(records)
        assert knowledge.revenue.pattern is GrowthPattern.INSUFFICIENT_DATA


class TestDurability:
    def test_consecutive_growth_periods_counts_trailing_growth(self):
        records = (
            _period(2020, revenue=1000.0), _period(2021, revenue=900.0), _period(2022, revenue=1000.0),
            _period(2023, revenue=1100.0), _period(2024, revenue=1250.0),
        )
        knowledge = _knowledge(records)
        assert knowledge.revenue.durability.consecutive_growth_periods == 3

    def test_recovered_after_a_decline(self):
        records = (_period(2021, revenue=1000.0), _period(2022, revenue=800.0), _period(2023, revenue=900.0))
        knowledge = _knowledge(records)
        assert knowledge.revenue.durability.recovery_status is RecoveryStatus.RECOVERED

    def test_currently_declining(self):
        records = (_period(2022, revenue=1000.0), _period(2023, revenue=800.0))
        knowledge = _knowledge(records)
        assert knowledge.revenue.durability.recovery_status is RecoveryStatus.CURRENTLY_DECLINING

    def test_no_decline_observed(self):
        records = (_period(2022, revenue=1000.0), _period(2023, revenue=1100.0))
        knowledge = _knowledge(records)
        assert knowledge.revenue.durability.recovery_status is RecoveryStatus.NO_DECLINE_OBSERVED

    def test_earnings_consistency_uses_the_value_based_rule(self):
        records = (
            _period(2021, net_income=100.0), _period(2022, net_income=150.0), _period(2023, net_income=200.0),
        )
        knowledge = _knowledge(records)
        assert knowledge.earnings.durability.consistency is GrowthConsistency.CONSISTENT_GROWTH


class TestConsistencyCrossCheck:
    """`growth_intelligence.py`'s own `_consistency_from_values` never
    imports `analysis_engine.growth.classify_metric_trend` (a real,
    enforced architecture boundary -- see that module's own docstring)
    -- this class verifies the two independent implementations still
    agree, using the real function only here, in the test file, which
    sits outside the restricted `atlas/alpha/investment_case/` package."""

    def test_consistent_growth_matches_the_real_evaluators_own_function(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2022-12-31"),
            fact(BusinessFactKind.REVENUE, 1100, "2023-12-31"),
            fact(BusinessFactKind.REVENUE, 1250, "2024-12-31"),
        )
        expected_trend, _, _ = classify_metric_trend(sorted(facts, key=lambda f: f.period))
        assert expected_trend is MetricTrend.STRONG_METRIC

        records = (_period(2022, revenue=1000.0), _period(2023, revenue=1100.0), _period(2024, revenue=1250.0))
        knowledge = _knowledge(records)
        assert knowledge.revenue.durability.consistency is GrowthConsistency.CONSISTENT_GROWTH

    def test_mixed_growth_matches_the_real_evaluators_own_function(self):
        facts = (
            fact(BusinessFactKind.REVENUE, 1000, "2022-12-31"),
            fact(BusinessFactKind.REVENUE, 900, "2023-12-31"),
            fact(BusinessFactKind.REVENUE, 1250, "2024-12-31"),
        )
        expected_trend, _, _ = classify_metric_trend(sorted(facts, key=lambda f: f.period))
        assert expected_trend is MetricTrend.MIXED_METRIC

        records = (_period(2022, revenue=1000.0), _period(2023, revenue=900.0), _period(2024, revenue=1250.0))
        knowledge = _knowledge(records)
        assert knowledge.revenue.durability.consistency is GrowthConsistency.MIXED

    def test_fewer_than_two_facts_is_insufficient_data_not_the_real_functions_own_vacuous_true(self):
        """`classify_metric_trend([])` itself returns `STRONG_METRIC`
        (vacuous `all()`) -- this module must not inherit that as
        "consistent growth" for a company with no real history."""
        knowledge = _knowledge(())
        assert knowledge.revenue.durability.consistency is GrowthConsistency.INSUFFICIENT_DATA

    def test_free_cash_flow_consistency_also_reuses_the_real_function(self):
        facts = (
            fact(BusinessFactKind.FREE_CASH_FLOW, 200, "2022-12-31"),
            fact(BusinessFactKind.FREE_CASH_FLOW, 150, "2023-12-31"),
        )
        expected_trend, _, _ = classify_metric_trend(sorted(facts, key=lambda f: f.period))
        assert expected_trend is MetricTrend.WEAK_METRIC

        records = (_period(2022, free_cash_flow=200.0), _period(2023, free_cash_flow=150.0))
        knowledge = _knowledge(records)
        assert knowledge.free_cash_flow.durability.consistency is GrowthConsistency.CONSISTENT_DECLINE


class TestSegmentGrowth:
    def test_always_unavailable(self):
        records = (_period(2023, revenue=1000.0),)
        knowledge = _knowledge(records)
        assert knowledge.segment_growth.available is False
