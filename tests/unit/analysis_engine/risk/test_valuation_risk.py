"""Tests for `atlas.analysis_engine.risk.valuation_risk.evaluate_valuation_risk`
(ATLAS-025 Phase 8) -- the documented rule table, including the
explicitly confirmed UNDERVALUED -> LOW mapping."""
from __future__ import annotations

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus
from atlas.analysis_engine.risk.valuation_risk import evaluate_valuation_risk
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.risk._fixtures import EVALUATED_AT, fcf_yield_finding


class TestRuleTable:
    def test_insufficient_input_is_insufficient_input_risk(self):
        finding = fcf_yield_finding(ValuationStatus.INSUFFICIENT_INPUT)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.INSUFFICIENT_INPUT
        assert RiskDataGapKind.VALUATION_ASSESSMENT_UNAVAILABLE in result.missing_evidence

    def test_not_evaluated_is_also_insufficient_input_risk(self):
        finding = fcf_yield_finding(ValuationStatus.NOT_EVALUATED)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.INSUFFICIENT_INPUT

    def test_expensive_is_high_risk(self):
        finding = fcf_yield_finding(ValuationStatus.EXPENSIVE)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH

    def test_fairly_valued_is_moderate_risk(self):
        finding = fcf_yield_finding(ValuationStatus.FAIRLY_VALUED)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.MODERATE

    def test_undervalued_is_low_risk(self):
        """Explicitly confirmed mapping: 'the specific risk of
        overpaying is low' for a company priced below its own
        historical range."""
        finding = fcf_yield_finding(ValuationStatus.UNDERVALUED)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW


class TestNeverRecomputesValuation:
    def test_evaluator_never_imports_cash_flow_module(self):
        """Prose in the module docstring may reference `valuation.cash_flow`
        by name (explaining what it must *not* do) -- only real `import`/
        `from` lines are checked, the same distinction
        `tests/unit/analysis_engine/valuation/test_boundaries.py` already
        draws between `_FORBIDDEN_ANYWHERE` and `_FORBIDDEN_IN_IMPORTS`."""
        import inspect

        from atlas.analysis_engine.risk import valuation_risk

        import_lines = [
            line
            for line in inspect.getsource(valuation_risk).splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        for line in import_lines:
            assert "cash_flow" not in line
            assert "evaluate_fcf_yield_relative" not in line

    def test_no_hardcoded_yield_or_multiple_threshold(self):
        import inspect

        from atlas.analysis_engine.risk import valuation_risk

        source = inspect.getsource(valuation_risk)
        for forbidden in ("0.05", "0.15", "price_to_earnings"):
            assert forbidden not in source


class TestTraceability:
    def test_category_and_id_are_correct(self):
        finding = fcf_yield_finding(ValuationStatus.EXPENSIVE)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.category is RiskCategory.VALUATION_RISK
        assert result.id == "risk_finding:valuation_risk"

    def test_valuation_finding_id_is_a_supporting_fact_and_dependency(self):
        finding = fcf_yield_finding(ValuationStatus.EXPENSIVE)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert finding.id in result.supporting_facts
        assert finding.id in result.provenance.dependencies

    def test_confidence_reuses_valuation_findings_confidence_verbatim(self):
        finding = fcf_yield_finding(ValuationStatus.EXPENSIVE, confidence=EvidenceCoverageLevel.PARTIAL)
        result = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.confidence is EvidenceCoverageLevel.PARTIAL


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_finding(self):
        finding = fcf_yield_finding(ValuationStatus.FAIRLY_VALUED)
        first = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        second = evaluate_valuation_risk(finding, evaluated_at=EVALUATED_AT)
        assert first == second
