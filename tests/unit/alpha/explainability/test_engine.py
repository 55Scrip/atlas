"""Tests for `atlas.alpha.explainability.engine` -- `Stance`/
`CoverageAssessment` are hand-built, controlled stand-ins for already-
tested-elsewhere upstream engines (the same convention
`tests/unit/alpha/stance/test_engine.py`'s own `_high_confidence_coverage`
fixture establishes), since this module's whole job is reclassifying
their fields, never recomputing them.
"""
from __future__ import annotations

from atlas.alpha.coverage import ConfidenceLevel, ConfidenceReason, ConfidenceReasonCode, CoverageAssessment, DimensionCoverage, DimensionCoverageLevel
from atlas.alpha.explainability import compare_evidence, explain
from atlas.alpha.stance import Stance, StanceLevel, StanceReason, StanceReasonCode
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel


def _dim(dimension: str, level: DimensionCoverageLevel = DimensionCoverageLevel.UNAVAILABLE, reasoning: tuple[str, ...] = ()) -> DimensionCoverage:
    return DimensionCoverage(dimension=dimension, level=level, reasoning=reasoning)


def _coverage(dimensions=(), missing=(), reasoning=()) -> CoverageAssessment:
    return CoverageAssessment(
        dimensions=dimensions,
        overall_coverage=AnalysisCoverageLevel.PARTIAL_COVERAGE,
        overall_confidence=ConfidenceLevel.MODERATE,
        missing_dimensions=missing,
        not_applicable_dimensions=(),
        reasoning=reasoning,
    )


def _stance(level, reasoning=(), supporting=(), limiting=(), missing=()) -> Stance:
    return Stance(
        level=level,
        reasoning=reasoning,
        supporting_signals=supporting,
        limiting_signals=limiting,
        confidence=ConfidenceLevel.MODERATE,
        missing_information=missing,
    )


class TestExplainClassification:
    def test_supporting_evidence_is_reused_verbatim_from_stance(self):
        supporting = (StanceReason(StanceReasonCode.THESIS_STRENGTHENED), StanceReason(StanceReasonCode.NO_HIGH_RISK))
        stance = _stance(StanceLevel.INCREASE, reasoning=supporting, supporting=supporting)
        explanation = explain(stance, _coverage())
        assert explanation.supporting_evidence == supporting

    def test_contradicting_evidence_excludes_gate_reasons(self):
        """A weak Portfolio Fit is a real directional negative; a low-
        confidence gate is not the same fact and must not appear here."""
        limiting = (StanceReason(StanceReasonCode.PORTFOLIO_FIT_WEAK), StanceReason(StanceReasonCode.CONFIDENCE_MODERATE))
        stance = _stance(StanceLevel.REVIEW, reasoning=limiting, limiting=limiting)
        explanation = explain(stance, _coverage())
        codes = {r.code for r in explanation.contradicting_evidence}
        assert codes == {StanceReasonCode.PORTFOLIO_FIT_WEAK}

    def test_limiting_factors_isolates_the_gate_reason(self):
        limiting = (StanceReason(StanceReasonCode.PORTFOLIO_FIT_WEAK), StanceReason(StanceReasonCode.CONFIDENCE_MODERATE))
        stance = _stance(StanceLevel.REVIEW, reasoning=limiting, limiting=limiting)
        explanation = explain(stance, _coverage())
        codes = {r.code for r in explanation.limiting_factors}
        assert codes == {StanceReasonCode.CONFIDENCE_MODERATE}

    def test_confidence_drivers_reused_verbatim_from_coverage(self):
        reasoning = (ConfidenceReason(ConfidenceReasonCode.DIMENSIONS_CONCLUSIVE, count=3, total=7),)
        coverage = _coverage(reasoning=reasoning)
        stance = _stance(StanceLevel.WAIT, reasoning=(StanceReason(StanceReasonCode.CONFIDENCE_LIMITED),))
        explanation = explain(stance, coverage)
        assert explanation.confidence_drivers == reasoning

    def test_missing_evidence_carries_the_real_dimension_coverage_not_just_the_key(self):
        growth = _dim("growth", reasoning=("insufficient_historical_periods",))
        coverage = _coverage(dimensions=(growth,), missing=("growth",))
        stance = _stance(StanceLevel.WAIT, missing=("growth",))
        explanation = explain(stance, coverage)
        assert explanation.missing_evidence == (growth,)
        assert explanation.missing_evidence[0].reasoning == ("insufficient_historical_periods",)


class TestMostValuableMissingInformation:
    def test_fcf_yield_relative_outranks_growth(self):
        growth = _dim("growth")
        fcf = _dim("fcf_yield_relative")
        coverage = _coverage(dimensions=(growth, fcf), missing=("growth", "fcf_yield_relative"))
        stance = _stance(StanceLevel.WAIT, missing=("growth", "fcf_yield_relative"))
        explanation = explain(stance, coverage)
        assert explanation.most_valuable_missing_information == fcf

    def test_growth_outranks_a_derived_risk_category(self):
        growth = _dim("growth")
        financial_risk = _dim("financial_risk")
        coverage = _coverage(dimensions=(growth, financial_risk), missing=("growth", "financial_risk"))
        stance = _stance(StanceLevel.WAIT, missing=("growth", "financial_risk"))
        explanation = explain(stance, coverage)
        assert explanation.most_valuable_missing_information == growth

    def test_none_when_nothing_is_missing(self):
        stance = _stance(StanceLevel.MAINTAIN)
        explanation = explain(stance, _coverage())
        assert explanation.most_valuable_missing_information is None

    def test_ordering_is_deterministic_regardless_of_input_order(self):
        growth = _dim("growth")
        fcf = _dim("fcf_yield_relative")
        coverage_a = _coverage(dimensions=(growth, fcf), missing=("growth", "fcf_yield_relative"))
        coverage_b = _coverage(dimensions=(fcf, growth), missing=("fcf_yield_relative", "growth"))
        stance = _stance(StanceLevel.WAIT, missing=("growth", "fcf_yield_relative"))
        assert explain(stance, coverage_a).most_valuable_missing_information == explain(stance, coverage_b).most_valuable_missing_information


class TestCompareEvidence:
    def test_a_favoring_signal_absent_from_b_counts_as_favoring_a(self):
        exp_a = explain(
            _stance(StanceLevel.INCREASE, reasoning=(StanceReason(StanceReasonCode.THESIS_STRENGTHENED),), supporting=(StanceReason(StanceReasonCode.THESIS_STRENGTHENED),)),
            _coverage(),
        )
        exp_b = explain(_stance(StanceLevel.MAINTAIN), _coverage())
        comparison = compare_evidence(exp_a, exp_b)
        assert {r.code for r in comparison.favoring_a} == {StanceReasonCode.THESIS_STRENGTHENED}
        assert comparison.favoring_b == ()

    def test_a_positive_b_negative_on_the_same_code_counts_as_favoring_a(self):
        exp_a = explain(
            _stance(StanceLevel.MAINTAIN, reasoning=(StanceReason(StanceReasonCode.NO_HIGH_RISK),), supporting=(StanceReason(StanceReasonCode.NO_HIGH_RISK),)),
            _coverage(),
        )
        exp_b = explain(
            _stance(StanceLevel.REVIEW, reasoning=(StanceReason(StanceReasonCode.HIGH_RISK_PRESENT),), limiting=(StanceReason(StanceReasonCode.HIGH_RISK_PRESENT),)),
            _coverage(),
        )
        comparison = compare_evidence(exp_a, exp_b)
        assert {r.code for r in comparison.favoring_a} == {StanceReasonCode.NO_HIGH_RISK}

    def test_a_shared_positive_signal_is_never_double_counted_as_favoring_either(self):
        shared_signal = (StanceReason(StanceReasonCode.NO_HIGH_RISK),)
        exp_a = explain(_stance(StanceLevel.MAINTAIN, reasoning=shared_signal, supporting=shared_signal), _coverage())
        exp_b = explain(_stance(StanceLevel.MAINTAIN, reasoning=shared_signal, supporting=shared_signal), _coverage())
        comparison = compare_evidence(exp_a, exp_b)
        assert comparison.favoring_a == ()
        assert comparison.favoring_b == ()
        assert {r.code for r in comparison.shared} == {StanceReasonCode.NO_HIGH_RISK}

    def test_missing_for_both_is_the_real_dimension_intersection(self):
        growth = _dim("growth")
        thesis = _dim("thesis_risk")
        exp_a = explain(
            _stance(StanceLevel.WAIT, missing=("growth", "thesis_risk")),
            _coverage(dimensions=(growth, thesis), missing=("growth", "thesis_risk")),
        )
        exp_b = explain(
            _stance(StanceLevel.WAIT, missing=("growth",)),
            _coverage(dimensions=(growth,), missing=("growth",)),
        )
        comparison = compare_evidence(exp_a, exp_b)
        assert comparison.missing_for_both == ("growth",)


class TestDeterminism:
    def test_identical_inputs_produce_deeply_equal_explanations(self):
        stance = _stance(StanceLevel.MAINTAIN, reasoning=(StanceReason(StanceReasonCode.THESIS_UNCHANGED),))
        coverage = _coverage()
        assert explain(stance, coverage) == explain(stance, coverage)
