"""Tests for `atlas.analysis_engine.recommendation_conviction` (`DE-004`
§3; "Recommendation Backend Step 2").

Confirms the Recommendation-specific Atlas Conviction Level is a genuinely
independent computation from the existing five-level
`atlas.analysis_engine.conviction.ConvictionLevel` -- never a relabeling,
never silently derived from it, never sharing its enum. Also confirms the
Recommendation stage itself is completely unaffected: `RecommendationWithheld`
behaviour is unchanged, and this new module is not consumed anywhere yet.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.recommendation import evaluate_recommendation_gate
from atlas.analysis_engine.recommendation_conviction import (
    RecommendationConvictionAssessment,
    RecommendationConvictionLevel,
    RecommendationConvictionReasonCode,
    calculate_recommendation_conviction,
)
from atlas.decision_engine.contracts import (
    EvaluationState,
    EvidenceCoverageLevel,
    RecommendationOutcomeKind,
)
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated

EVALUATED = EvaluationState.EVALUATED
NOT_EVALUATED = EvaluationState.NOT_EVALUATED

_ALL_EVALUATED = dict(
    business_state=EVALUATED,
    valuation_state=EVALUATED,
    portfolio_intelligence_state=EVALUATED,
)


def _call(**overrides):
    fields = dict(
        business_state=EVALUATED,
        valuation_state=EVALUATED,
        portfolio_intelligence_state=EVALUATED,
        reasoning_state=EVALUATED,
        evidence_coverage=EvidenceCoverageLevel.FULL,
        has_contradicting_evidence=False,
        has_open_questions=False,
    )
    fields.update(overrides)
    return calculate_recommendation_conviction(**fields)


class TestHigh:
    def test_full_coverage_no_contradiction_no_open_questions_is_high(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            has_contradicting_evidence=False,
            has_open_questions=False,
        )
        assert result is not None
        assert result.level is RecommendationConvictionLevel.HIGH

    def test_high_names_every_applicable_reason(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            has_contradicting_evidence=False,
            has_open_questions=False,
        )
        assert result.reasons == (
            RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
            RecommendationConvictionReasonCode.NO_CONTRADICTING_EVIDENCE,
            RecommendationConvictionReasonCode.NO_OPEN_QUESTIONS,
        )


class TestMedium:
    def test_full_coverage_with_contradiction_is_medium(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            has_contradicting_evidence=True,
            has_open_questions=False,
        )
        assert result.level is RecommendationConvictionLevel.MEDIUM

    def test_full_coverage_with_open_questions_is_medium(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            has_contradicting_evidence=False,
            has_open_questions=True,
        )
        assert result.level is RecommendationConvictionLevel.MEDIUM

    def test_full_coverage_with_both_is_still_medium_not_lower(self):
        """No fourth, worse-than-Medium tier exists for "both present" --
        DE-004 §3 names exactly three levels."""
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            has_contradicting_evidence=True,
            has_open_questions=True,
        )
        assert result.level is RecommendationConvictionLevel.MEDIUM

    def test_medium_names_every_applicable_reason(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            has_contradicting_evidence=True,
            has_open_questions=True,
        )
        assert result.reasons == (
            RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
            RecommendationConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT,
            RecommendationConvictionReasonCode.OPEN_QUESTIONS_REMAIN,
        )


class TestLow:
    def test_partial_coverage_is_low_regardless_of_contradiction(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.PARTIAL,
            has_contradicting_evidence=True,
            has_open_questions=True,
        )
        assert result.level is RecommendationConvictionLevel.LOW

    def test_partial_coverage_is_low_even_with_no_other_issues(self):
        result = _call(
            evidence_coverage=EvidenceCoverageLevel.PARTIAL,
            has_contradicting_evidence=False,
            has_open_questions=False,
        )
        assert result.level is RecommendationConvictionLevel.LOW

    def test_low_names_the_coverage_reason(self):
        result = _call(evidence_coverage=EvidenceCoverageLevel.PARTIAL)
        assert result.reasons == (RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL,)


class TestBoundaryTransitions:
    """DE-004 §4 -- insufficient evidence precedes the scale entirely; it
    is never a fourth enum member."""

    @pytest.mark.parametrize(
        "coverage", [EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE]
    )
    def test_no_or_not_applicable_coverage_returns_none(self, coverage):
        assert _call(evidence_coverage=coverage) is None

    @pytest.mark.parametrize(
        "field",
        ["business_state", "valuation_state", "portfolio_intelligence_state", "reasoning_state"],
    )
    def test_any_stage_not_evaluated_returns_none(self, field):
        assert _call(**{field: NOT_EVALUATED}) is None

    def test_partial_to_full_is_the_low_to_medium_or_high_boundary(self):
        low = _call(evidence_coverage=EvidenceCoverageLevel.PARTIAL, has_contradicting_evidence=False)
        high = _call(evidence_coverage=EvidenceCoverageLevel.FULL, has_contradicting_evidence=False)
        assert low.level is RecommendationConvictionLevel.LOW
        assert high.level is RecommendationConvictionLevel.HIGH

    def test_none_never_returns_a_fourth_enum_member(self):
        """There is no INSUFFICIENT/UNKNOWN/NOT_EVALUATED member on
        RecommendationConvictionLevel at all -- the function returns the
        Python value None, never a member of the enum, for that case."""
        assert len(RecommendationConvictionLevel) == 3
        assert {m.value for m in RecommendationConvictionLevel} == {"high", "medium", "low"}


class TestDeterministicBehaviour:
    def test_identical_inputs_produce_equal_results(self):
        first = _call(evidence_coverage=EvidenceCoverageLevel.FULL, has_open_questions=True)
        second = _call(evidence_coverage=EvidenceCoverageLevel.FULL, has_open_questions=True)
        assert first == second
        assert first is not second  # equal, not the same object -- no caching/memoization

    def test_no_wall_clock_or_randomness_dependency(self):
        """The function signature carries no timestamp/clock parameter at
        all -- unlike calculate_conviction's caller-supplied determinism
        pattern, this function needs no time input because it produces
        no timestamped output."""
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert "generated_at" not in params
        assert "now" not in params


class TestInvalidConstruction:
    def test_level_must_be_the_new_enum(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationConvictionAssessment(
                level=ConvictionLevel.HIGH,  # the OTHER (five-level) enum
                reasons=(RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,),
            )

    def test_level_rejects_bare_string(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationConvictionAssessment(level="high", reasons=(RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,))

    def test_reasons_must_be_non_empty(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationConvictionAssessment(level=RecommendationConvictionLevel.HIGH, reasons=())

    def test_reasons_must_contain_only_reason_codes(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationConvictionAssessment(
                level=RecommendationConvictionLevel.HIGH, reasons=("evidence_coverage_full",)
            )


class TestEquality:
    def test_same_values_are_equal(self):
        a = RecommendationConvictionAssessment(
            level=RecommendationConvictionLevel.MEDIUM,
            reasons=(RecommendationConvictionReasonCode.OPEN_QUESTIONS_REMAIN,),
        )
        b = RecommendationConvictionAssessment(
            level=RecommendationConvictionLevel.MEDIUM,
            reasons=(RecommendationConvictionReasonCode.OPEN_QUESTIONS_REMAIN,),
        )
        assert a == b

    def test_different_levels_are_not_equal(self):
        a = RecommendationConvictionAssessment(
            level=RecommendationConvictionLevel.HIGH,
            reasons=(RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,),
        )
        b = RecommendationConvictionAssessment(
            level=RecommendationConvictionLevel.MEDIUM,
            reasons=(RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_FULL,),
        )
        assert a != b

    def test_frozen_is_immutable(self):
        result = _call()
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.level = RecommendationConvictionLevel.LOW  # type: ignore[misc]


class TestSerialization:
    """No API layer exists for this yet (explicitly out of scope) -- this
    only confirms the type is structurally serialization-ready: plain
    dataclass fields, plain string enum values, no exotic types."""

    def test_asdict_produces_plain_values(self):
        result = _call(has_contradicting_evidence=True)
        as_dict = dataclasses.asdict(result)
        assert as_dict["level"] == RecommendationConvictionLevel.MEDIUM
        assert isinstance(as_dict["level"].value, str)
        assert all(isinstance(r.value, str) for r in as_dict["reasons"])

    def test_enum_values_round_trip_through_their_string_value(self):
        for level in RecommendationConvictionLevel:
            assert RecommendationConvictionLevel(level.value) is level
        for reason in RecommendationConvictionReasonCode:
            assert RecommendationConvictionReasonCode(reason.value) is reason


class TestNoDependencyOnDirection:
    def test_function_signature_has_no_direction_parameter(self):
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert "direction" not in params

    def test_assessment_has_no_direction_field(self):
        result = _call()
        assert not hasattr(result, "direction")


class TestNoDependencyOnExecutionGuidance:
    def test_function_signature_has_no_execution_guidance_parameters(self):
        params = set(inspect.signature(calculate_recommendation_conviction).parameters)
        forbidden = {
            "execution_guidance",
            "target_allocation_range",
            "execution_range",
            "accumulation_approach",
            "urgency",
        }
        assert not (params & forbidden)

    def test_module_does_not_import_anything_execution_guidance_shaped(self):
        import atlas.analysis_engine.recommendation_conviction as module

        source = inspect.getsource(module)
        assert "ExecutionGuidance" not in source


def _insufficient_business_analysis(output):
    """Growth/Capital Allocation both `INSUFFICIENT_INPUT` -- no
    `business_records` supplied, matching every real call site's default.
    Mirrors `test_recommendation.py`'s own identically-named helper."""
    from atlas.analysis_engine.business import evaluate_business_analysis

    return evaluate_business_analysis(output.business_evaluation, business_records=(), evaluated_at=GENERATED_AT)


def _insufficient_valuation_engine():
    from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
    from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
    from atlas.analysis_engine.valuation.pipeline import evaluate_valuation

    business_facts = extract_facts_from_records((), evaluated_at=GENERATED_AT)
    market_facts = extract_valuation_facts_from_records((), evaluated_at=GENERATED_AT)
    return evaluate_valuation(business_facts, market_facts, evaluated_at=GENERATED_AT)


def _insufficient_valuation_support():
    """`DE-016`: `evaluate_recommendation_gate` now requires this
    parameter -- `INSUFFICIENT_INPUT` is the correct default for every
    call in this file, none of which is exercising the new BUY/ADD
    wiring (that lives in `test_recommendation.py::TestBuyAddNowWired`)."""
    from atlas.analysis_engine.valuation.support import ValuationSupport, ValuationSupportGapKind, ValuationSupportStatus

    return ValuationSupport(
        status=ValuationSupportStatus.INSUFFICIENT_INPUT,
        reasoning="No real data supplied in this fixture.",
        gap=ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA,
    )


class TestRecommendationWithheldWhenBusinessInconclusive:
    """Renamed from `TestRecommendationWithheldRegressionUnchanged`:
    `atlas.analysis_engine.recommendation_conviction` is now consumed by
    `evaluate_recommendation_gate` for real ("Recommendation Backend Step
    3") -- the `test_gate_function_does_not_call_the_new_conviction_module`
    regression guard this class previously enforced tested for the exact
    gap this sprint closes, and has been removed rather than kept
    failing. What remains true, and is still asserted here: these
    specific business-inconclusive fixtures (`run_populated`/
    `run_minimal`, no real Growth/Capital Allocation facts) still produce
    RecommendationWithheld -- via the real Direction Selector now
    returning `None`, not via a hardcoded gap."""

    def test_still_withheld_when_business_is_inconclusive(self):
        engine_input, output = run_populated()
        conviction = ConvictionAssessment(level=ConvictionLevel.VERY_HIGH, reasons=())
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=conviction,
            business_analysis=_insufficient_business_analysis(output),
            valuation_engine=_insufficient_valuation_engine(),
            valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_minimal_input_also_still_withholds(self):
        engine_input, output = run_minimal()
        conviction = ConvictionAssessment(level=ConvictionLevel.INSUFFICIENT_EVIDENCE, reasons=())
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=conviction,
            business_analysis=_insufficient_business_analysis(output),
            valuation_engine=_insufficient_valuation_engine(),
            valuation_support=_insufficient_valuation_support(),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_gate_function_now_calls_the_conviction_module(self):
        """Inverted from the pre-Step-3 regression guard: this module is
        now genuinely consumed, and this test documents that fact rather
        than the gap it replaces."""
        import atlas.analysis_engine.recommendation as recommendation_module

        source = inspect.getsource(recommendation_module.evaluate_recommendation_gate)
        assert "calculate_recommendation_conviction" in source
