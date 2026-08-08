"""Tests for `atlas.analysis_engine.valuation.models` (ATLAS-024 Phase
9) -- contract validation and immutability."""
from __future__ import annotations

import dataclasses

from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.decision_engine.contracts import EvaluationState
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT


class TestValuationEngineResultContract:
    def test_rejects_a_partial_method_list(self):
        result = evaluate_valuation((), (), evaluated_at=EVALUATED_AT)
        incomplete = result.findings[:1]
        try:
            ValuationEngineResult(state=EvaluationState.EVALUATED, findings=incomplete)
            assert False, "expected AnalysisEngineContractError"
        except AnalysisEngineContractError:
            pass

    def test_accepts_all_four_methods(self):
        result = evaluate_valuation((), (), evaluated_at=EVALUATED_AT)
        assert len(result.findings) == 4
        assert result.state is EvaluationState.EVALUATED


class TestImmutability:
    def test_valuation_finding_is_frozen(self):
        result = evaluate_valuation((), (), evaluated_at=EVALUATED_AT)
        try:
            result.findings[0].status = ValuationStatus.UNDERVALUED
            assert False, "expected FrozenInstanceError"
        except dataclasses.FrozenInstanceError:
            pass


class TestNoTopLevelSummaryStatus:
    def test_valuation_engine_result_has_no_status_field(self):
        """Mirrors BusinessAnalysisResult's own choice -- callers inspect
        findings individually, never a collapsed summary."""
        field_names = {f.name for f in dataclasses.fields(ValuationEngineResult)}
        assert "status" not in field_names


class TestFindingKindIsDistinctFromDecisionEngine:
    def test_no_naming_collision_at_runtime(self):
        from atlas.analysis_engine.valuation.models import ValuationFinding as EngineValuationFinding
        from atlas.decision_engine.contracts import ValuationFinding as LockedValuationFinding

        assert EngineValuationFinding is not LockedValuationFinding
        engine_fields = {f.name for f in dataclasses.fields(EngineValuationFinding)}
        assert "status" in engine_fields
        locked_fields = {f.name for f in dataclasses.fields(LockedValuationFinding)}
        assert "status" not in locked_fields
        assert set(engine_fields).isdisjoint({"fair_value", "cheap", "expensive", "target_price"})
