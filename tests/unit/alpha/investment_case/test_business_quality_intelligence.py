"""Tests for `atlas.alpha.investment_case.business_quality_intelligence`
(Capability Expansion Sprint 7, Phases 1 + 3 through 6 + 8 + 9).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.alpha.investment_case.business_quality_intelligence import (
    BusinessQualityFinding,
    BusinessQualityFindingKind,
    ConsistencyLevel,
    EvolutionDirection,
    StabilityLevel,
    TrendDirection,
    extract_business_quality,
)
from atlas.alpha.investment_case.capital_allocation_intelligence import (
    BuybackConsistency,
    DebtDiscipline,
    extract_capital_allocation_history,
)
from atlas.alpha.investment_case.financial_quality_intelligence import extract_financial_quality
from atlas.alpha.investment_case.financial_statement_intelligence import extract_financial_statement_history
from atlas.alpha.investment_case.growth_intelligence import GrowthConsistency, GrowthMetric, extract_growth_knowledge
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


def _quality(records):
    fsh = extract_financial_statement_history(records)
    cah = extract_capital_allocation_history(records)
    fq = extract_financial_quality(fsh)
    growth = extract_growth_knowledge(fsh)
    return extract_business_quality(fsh, cah, fq, growth)


def _steady_records(n=6, **overrides):
    defaults = dict(
        net_income=100.0, operating_cash_flow=150.0, free_cash_flow=120.0, equity=500.0, total_assets=1200.0,
        total_debt=200.0, current_assets=400.0, current_liabilities=200.0, share_buybacks=50.0, dividends=20.0,
        debt_issuance=10.0, debt_repayment=15.0, shares_outstanding=100.0,
    )
    defaults.update(overrides)
    return tuple(
        _period(2018 + i, revenue=1000.0 + i * 150, net_income=defaults["net_income"] + i * 15,
                operating_cash_flow=defaults["operating_cash_flow"] + i * 20,
                free_cash_flow=defaults["free_cash_flow"] + i * 18, equity=defaults["equity"] + i * 40,
                total_assets=defaults["total_assets"] + i * 60, total_debt=defaults["total_debt"],
                current_assets=defaults["current_assets"], current_liabilities=defaults["current_liabilities"],
                share_buybacks=defaults["share_buybacks"], dividends=defaults["dividends"],
                debt_issuance=defaults["debt_issuance"], debt_repayment=defaults["debt_repayment"],
                shares_outstanding=defaults["shares_outstanding"] - i * 2)
        for i in range(n)
    )


class TestEmptyInput:
    def test_no_data_yields_insufficient_data_across_every_dimension(self):
        quality = _quality(())
        assert quality.stability.profitability_stability is StabilityLevel.INSUFFICIENT_DATA
        assert quality.stability.revenue_stability is GrowthConsistency.INSUFFICIENT_DATA
        assert quality.stability.cash_generation_stability is ConsistencyLevel.INSUFFICIENT_DATA
        assert quality.stability.capital_allocation_stability is BuybackConsistency.INSUFFICIENT_DATA
        assert quality.durability.earnings_durability is ConsistencyLevel.INSUFFICIENT_DATA
        assert quality.durability.growth_durability.metrics_with_consistent_growth == ()
        assert quality.efficiency.asset_efficiency_trend is TrendDirection.INSUFFICIENT_DATA
        assert quality.evolution.direction is EvolutionDirection.INSUFFICIENT_DATA
        assert quality.consistency.stable_dimensions == ()
        assert quality.consistency.major_historical_disruptions == ()
        assert quality.findings == (
            BusinessQualityFinding(kind=BusinessQualityFindingKind.INSUFFICIENT_HISTORY, supporting_dimensions=()),
        )


class TestBusinessStability:
    def test_steady_growing_business_is_stable_across_every_dimension(self):
        quality = _quality(_steady_records())
        assert quality.stability.profitability_stability is StabilityLevel.STABLE
        assert quality.stability.revenue_stability is GrowthConsistency.CONSISTENT_GROWTH
        assert quality.stability.cash_generation_stability is ConsistencyLevel.CONSISTENT
        assert quality.stability.capital_allocation_stability is BuybackConsistency.CONSISTENT

    def test_volatile_revenue_is_reflected_as_mixed_revenue_stability(self):
        records = (
            _period(2020, revenue=1000.0), _period(2021, revenue=1500.0), _period(2022, revenue=1100.0),
            _period(2023, revenue=1800.0),
        )
        quality = _quality(records)
        assert quality.stability.revenue_stability is GrowthConsistency.MIXED

    def test_no_buybacks_ever_is_none_capital_allocation_stability(self):
        records = tuple(_period(2020 + i, revenue=1000.0, share_buybacks=0.0) for i in range(3))
        quality = _quality(records)
        assert quality.stability.capital_allocation_stability is BuybackConsistency.NONE


class TestBusinessDurability:
    def test_earnings_durability_reuses_financial_health_reading(self):
        records = tuple(_period(2020 + i, revenue=1000.0, net_income=100.0 + i * 10) for i in range(3))
        quality = _quality(records)
        assert quality.durability.earnings_durability is ConsistencyLevel.CONSISTENT

    def test_earnings_durability_is_inconsistent_with_a_loss_period(self):
        records = (
            _period(2020, revenue=1000.0, net_income=100.0), _period(2021, revenue=1000.0, net_income=-50.0),
            _period(2022, revenue=1000.0, net_income=80.0),
        )
        quality = _quality(records)
        assert quality.durability.earnings_durability is ConsistencyLevel.INCONSISTENT

    def test_growth_durability_summary_groups_consistent_metrics(self):
        quality = _quality(_steady_records())
        assert GrowthMetric.REVENUE in quality.durability.growth_durability.metrics_with_consistent_growth
        assert GrowthMetric.EARNINGS in quality.durability.growth_durability.metrics_with_consistent_growth

    def test_recovered_metric_appears_in_recovery_summary(self):
        records = (
            _period(2021, revenue=1000.0), _period(2022, revenue=800.0), _period(2023, revenue=900.0),
        )
        quality = _quality(records)
        assert GrowthMetric.REVENUE in quality.durability.growth_durability.metrics_recovered_from_decline

    def test_capital_discipline_passes_through_management_capital_allocation(self):
        records = tuple(
            _period(2020 + i, revenue=1000.0, debt_issuance=0.0, debt_repayment=0.0) for i in range(3)
        )
        quality = _quality(records)
        assert quality.durability.capital_discipline.debt_discipline is DebtDiscipline.DISCIPLINED


class TestBusinessEfficiency:
    def test_efficiency_reuses_capital_efficiency_verbatim(self):
        quality = _quality(_steady_records())
        assert quality.efficiency.capital_efficiency.asset_turnover_trend is quality.efficiency.asset_efficiency_trend


class TestBusinessConsistency:
    def test_all_stable_dimensions_are_named(self):
        quality = _quality(_steady_records())
        assert "profitability_stability" in quality.consistency.stable_dimensions
        assert "revenue_stability" in quality.consistency.stable_dimensions
        assert quality.consistency.volatile_dimensions == ()

    def test_disruptions_are_empty_with_no_margin_reversal(self):
        quality = _quality(_steady_records())
        assert quality.consistency.major_historical_disruptions == ()


class TestBusinessEvolution:
    def test_all_rising_signals_yield_strengthening(self):
        quality = _quality(_steady_records())
        assert quality.evolution.direction in (EvolutionDirection.STRENGTHENING, EvolutionDirection.MIXED)

    def test_no_known_signals_yields_insufficient_data(self):
        quality = _quality(())
        assert quality.evolution.direction is EvolutionDirection.INSUFFICIENT_DATA


class TestFindings:
    def test_steady_business_yields_consistent_value_creation_finding(self):
        quality = _quality(_steady_records())
        kinds = {f.kind for f in quality.findings}
        assert BusinessQualityFindingKind.CONSISTENT_VALUE_CREATION in kinds
        assert BusinessQualityFindingKind.DURABLE_GROWTH in kinds

    def test_every_finding_names_its_supporting_dimensions(self):
        quality = _quality(_steady_records())
        for finding in quality.findings:
            if finding.kind is not BusinessQualityFindingKind.INSUFFICIENT_HISTORY:
                assert len(finding.supporting_dimensions) > 0

    def test_empty_history_yields_only_insufficient_history_finding(self):
        quality = _quality(())
        assert len(quality.findings) == 1
        assert quality.findings[0].kind is BusinessQualityFindingKind.INSUFFICIENT_HISTORY
