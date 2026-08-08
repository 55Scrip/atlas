"""Tests for `atlas.analysis_engine.valuation.pipeline.evaluate_valuation`
(ATLAS-024 Phase 2/9) -- the orchestrator combining FCF Yield and the
three scenario findings."""
from __future__ import annotations

from datetime import date

from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.decision_engine.contracts import EvaluationState
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT, fundamentals_record, market_record


class TestStructuralCompleteness:
    def test_always_four_findings(self):
        result = evaluate_valuation((), (), evaluated_at=EVALUATED_AT)
        assert len(result.findings) == 4
        assert result.state is EvaluationState.EVALUATED

    def test_names_all_four_method_kinds(self):
        result = evaluate_valuation((), (), evaluated_at=EVALUATED_AT)
        assert {f.kind for f in result.findings} == set(ValuationMethodKind)


class TestEndToEndFromRealRecords:
    def test_real_records_produce_a_real_undervalued_finding(self):
        records = (
            fundamentals_record(period_end=date(2022, 12, 31), identifier="fy22", free_cash_flow=100.0),
            fundamentals_record(period_end=date(2023, 12, 31), identifier="fy23", free_cash_flow=110.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="fy24", free_cash_flow=200.0),
            market_record(period_end=date(2022, 12, 31), identifier="m22", share_price=50.0, shares_outstanding=100.0),
            market_record(period_end=date(2023, 12, 31), identifier="m23", share_price=52.0, shares_outstanding=100.0),
            market_record(period_end=date(2024, 12, 31), identifier="m24", share_price=53.0, shares_outstanding=100.0),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
        result = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)

        fcf_yield = next(f for f in result.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
        assert fcf_yield.status is ValuationStatus.UNDERVALUED

        scenarios = [f for f in result.findings if f.kind is not ValuationMethodKind.FCF_YIELD_RELATIVE]
        assert len(scenarios) == 3
        assert all(f.status is ValuationStatus.INSUFFICIENT_INPUT for f in scenarios)


class TestScenarioE_StrongGrowthExpensiveValuation:
    """Phase 19 Scenario E: Business Findings and Valuation Findings
    must stay independent -- neither is adjusted to agree with the
    other."""

    def test_growth_and_valuation_can_disagree(self):
        from atlas.analysis_engine.growth import evaluate_growth

        records = (
            fundamentals_record(period_end=date(2022, 12, 31), identifier="fy22", free_cash_flow=100.0),
            fundamentals_record(period_end=date(2023, 12, 31), identifier="fy23", free_cash_flow=150.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="fy24", free_cash_flow=250.0),
            market_record(period_end=date(2022, 12, 31), identifier="m22", share_price=10.0, shares_outstanding=100.0),
            market_record(period_end=date(2023, 12, 31), identifier="m23", share_price=10.0, shares_outstanding=100.0),
            market_record(period_end=date(2024, 12, 31), identifier="m24", share_price=90.0, shares_outstanding=100.0),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)

        growth_finding = evaluate_growth(business_facts, evaluated_at=EVALUATED_AT)
        valuation_result = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        fcf_yield = next(f for f in valuation_result.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)

        # FCF grew every period (STRONG-eligible single metric -> at
        # least MODERATE), while the price rocketed far more -> EXPENSIVE.
        assert fcf_yield.status is ValuationStatus.EXPENSIVE
        assert growth_finding.status.value in ("moderate", "strong")


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_result(self):
        records = (
            fundamentals_record(period_end=date(2023, 12, 31), identifier="fy23", free_cash_flow=100.0),
            fundamentals_record(period_end=date(2024, 12, 31), identifier="fy24", free_cash_flow=110.0),
            market_record(period_end=date(2023, 12, 31), identifier="m23", share_price=50.0, shares_outstanding=100.0),
            market_record(period_end=date(2024, 12, 31), identifier="m24", share_price=52.0, shares_outstanding=100.0),
        )
        business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
        valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
        first = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        second = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        assert first == second
