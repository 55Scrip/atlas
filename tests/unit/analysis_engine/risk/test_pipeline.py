"""Tests for `atlas.analysis_engine.risk.pipeline.evaluate_risk` (ATLAS-025
Phase 12/13) -- orchestration, Scenario E/F/G/H from Phase 21 (dimension
independence), and the "no aggregate label" invariant."""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES
from atlas.analysis_engine.risk.pipeline import evaluate_risk
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel, ObservationEpistemicStatus
from tests.unit.analysis_engine.risk._fixtures import (
    EVALUATED_AT,
    business_analysis_result,
    classification,
    contradiction_summary,
    valuation_engine_result,
)


def _evaluate(
    *,
    growth=BusinessCategoryStatus.INSUFFICIENT_INPUT,
    capital_allocation=BusinessCategoryStatus.INSUFFICIENT_INPUT,
    fcf_yield=ValuationStatus.INSUFFICIENT_INPUT,
    contradictions=(),
    evidence_coverage=EvidenceCoverageLevel.NOT_APPLICABLE,
):
    business_analysis = business_analysis_result(growth=growth, capital_allocation=capital_allocation)
    valuation_engine = valuation_engine_result(fcf_yield=fcf_yield)
    return evaluate_risk(
        business_analysis,
        (),
        valuation_engine,
        contradiction_summary(*contradictions),
        evidence_coverage=evidence_coverage,
        evaluated_at=EVALUATED_AT,
    )


class TestStructuralCompleteness:
    def test_state_is_always_evaluated(self):
        result = _evaluate()
        assert result.state is EvaluationState.EVALUATED

    def test_exactly_four_findings_naming_the_evaluated_categories(self):
        result = _evaluate()
        assert {f.category for f in result.findings} == EVALUATED_RISK_CATEGORIES

    def test_no_overall_aggregate_field_anywhere(self):
        result = _evaluate()
        assert not hasattr(result, "overall_status")
        assert not hasattr(result, "risk_score")


class TestScenarioE_StrongGrowthExpensiveValuation:
    def test_business_risk_low_valuation_risk_high_can_coexist(self):
        result = _evaluate(growth=BusinessCategoryStatus.STRONG, fcf_yield=ValuationStatus.EXPENSIVE)
        business = next(f for f in result.findings if f.category is RiskCategory.BUSINESS_RISK)
        valuation = next(f for f in result.findings if f.category is RiskCategory.VALUATION_RISK)
        assert business.status is RiskStatus.LOW
        assert valuation.status is RiskStatus.HIGH


class TestScenarioF_WeakGrowthCheapValuation:
    def test_business_risk_high_valuation_risk_low_can_coexist(self):
        result = _evaluate(growth=BusinessCategoryStatus.WEAK, fcf_yield=ValuationStatus.UNDERVALUED)
        business = next(f for f in result.findings if f.category is RiskCategory.BUSINESS_RISK)
        valuation = next(f for f in result.findings if f.category is RiskCategory.VALUATION_RISK)
        assert business.status is RiskStatus.HIGH
        assert valuation.status is RiskStatus.LOW


class TestScenarioG_ContradictionWithoutFundamentalData:
    def test_thesis_risk_and_data_gaps_are_reported_independently(self):
        classified = classification(ObservationEpistemicStatus.CONTRADICTED, challenging_count=1)
        result = _evaluate(
            contradictions=(classified,),
            evidence_coverage=EvidenceCoverageLevel.PARTIAL,
        )
        thesis = next(f for f in result.findings if f.category is RiskCategory.THESIS_RISK)
        business = next(f for f in result.findings if f.category is RiskCategory.BUSINESS_RISK)
        financial = next(f for f in result.findings if f.category is RiskCategory.FINANCIAL_RISK)
        assert thesis.status is RiskStatus.HIGH
        assert business.status is RiskStatus.INSUFFICIENT_INPUT
        assert financial.status is RiskStatus.INSUFFICIENT_INPUT


class TestScenarioH_ValuationUnavailable:
    def test_valuation_risk_is_insufficient_input(self):
        result = _evaluate(fcf_yield=ValuationStatus.NOT_EVALUATED)
        valuation = next(f for f in result.findings if f.category is RiskCategory.VALUATION_RISK)
        assert valuation.status is RiskStatus.INSUFFICIENT_INPUT


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_result(self):
        first = _evaluate(growth=BusinessCategoryStatus.MODERATE, fcf_yield=ValuationStatus.FAIRLY_VALUED)
        second = _evaluate(growth=BusinessCategoryStatus.MODERATE, fcf_yield=ValuationStatus.FAIRLY_VALUED)
        assert first == second
