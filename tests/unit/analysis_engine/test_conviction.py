"""Decision-table coverage for `atlas.analysis_engine.conviction
.calculate_conviction` (ATLAS-020 Phase 9; extended ATLAS-026 Phase 4)
-- every branch of the ordered if/elif chain, exercised directly
against its own inputs rather than through the full pipeline, so each
branch is isolated."""
from __future__ import annotations

from atlas.analysis_engine.conviction import (
    ConvictionLevel,
    ConvictionReasonCode,
    calculate_conviction,
)
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

_BASE_KWARGS = dict(
    business_state=EvaluationState.EVALUATED,
    valuation_state=EvaluationState.EVALUATED,
    evidence_coverage=EvidenceCoverageLevel.FULL,
    has_contradicting_evidence=False,
    has_open_questions=False,
    is_thesis_stale=False,
)


class TestUpstreamNotEvaluated:
    def test_business_not_evaluated_yields_insufficient_evidence(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "business_state": EvaluationState.NOT_EVALUATED})
        assert result.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert result.reasons == (ConvictionReasonCode.UPSTREAM_STAGE_NOT_EVALUATED,)

    def test_valuation_not_evaluated_yields_insufficient_evidence(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "valuation_state": EvaluationState.INSUFFICIENT_INPUT})
        assert result.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert result.reasons == (ConvictionReasonCode.UPSTREAM_STAGE_NOT_EVALUATED,)


class TestEvidenceCoverageInsufficient:
    def test_not_applicable_coverage_yields_insufficient_evidence(self):
        result = calculate_conviction(
            **{**_BASE_KWARGS, "evidence_coverage": EvidenceCoverageLevel.NOT_APPLICABLE}
        )
        assert result.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert result.reasons == (ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,)

    def test_none_coverage_yields_insufficient_evidence(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "evidence_coverage": EvidenceCoverageLevel.NONE})
        assert result.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert result.reasons == (ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,)


class TestLowConviction:
    def test_contradicting_evidence_yields_low_regardless_of_coverage(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "has_contradicting_evidence": True})
        assert result.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT in result.reasons

    def test_partial_coverage_without_contradiction_yields_low(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "evidence_coverage": EvidenceCoverageLevel.PARTIAL})
        assert result.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL in result.reasons


class TestHighFinancialOrValuationRiskLowersConviction:
    """ATLAS-026 Phase 4/7: Financial Risk or Valuation Risk at HIGH
    forces LOW, the same severity tier as contradicting evidence."""

    def test_high_risk_alone_yields_low_even_with_full_coverage(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "has_high_financial_or_valuation_risk": True})
        assert result.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT in result.reasons

    def test_no_high_risk_reason_is_present_when_false(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert ConvictionReasonCode.NO_HIGH_FINANCIAL_OR_VALUATION_RISK in result.reasons
        assert ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT not in result.reasons

    def test_high_risk_together_with_contradiction_still_yields_low_not_worse(self):
        """No tier below LOW exists for a "doubly bad" combination --
        this is a categorical model, not an additive one."""
        result = calculate_conviction(
            **{**_BASE_KWARGS, "has_contradicting_evidence": True, "has_high_financial_or_valuation_risk": True}
        )
        assert result.level is ConvictionLevel.LOW

    def test_high_risk_overrides_would_be_very_high(self):
        result = calculate_conviction(
            **_BASE_KWARGS,
            business_conclusive=True,
            valuation_conclusive=True,
            has_high_financial_or_valuation_risk=True,
        )
        assert result.level is ConvictionLevel.LOW


class TestModerateConviction:
    def test_stale_thesis_with_full_coverage_yields_moderate(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "is_thesis_stale": True})
        assert result.level is ConvictionLevel.MODERATE
        assert ConvictionReasonCode.THESIS_STALE in result.reasons

    def test_open_questions_with_full_coverage_yields_moderate(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "has_open_questions": True})
        assert result.level is ConvictionLevel.MODERATE
        assert ConvictionReasonCode.OPEN_QUESTIONS_REMAIN in result.reasons


class TestHighConviction:
    def test_full_coverage_no_contradiction_no_risk_no_staleness_no_open_questions_yields_high(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.level is ConvictionLevel.HIGH
        assert ConvictionReasonCode.BUSINESS_OR_VALUATION_NOT_YET_CONCLUSIVE in result.reasons

    def test_very_high_is_unreachable_with_default_conclusiveness(self):
        """`business_conclusive`/`valuation_conclusive` default `False`
        -- the best conviction any caller that doesn't pass them
        explicitly can reach is `HIGH`, never `VERY_HIGH`."""
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.level is not ConvictionLevel.VERY_HIGH


class TestVeryHighConviction:
    def test_conclusive_business_and_valuation_yields_very_high(self):
        result = calculate_conviction(
            **_BASE_KWARGS, business_conclusive=True, valuation_conclusive=True
        )
        assert result.level is ConvictionLevel.VERY_HIGH
        assert ConvictionReasonCode.BUSINESS_AND_VALUATION_CONCLUSIVE in result.reasons

    def test_only_one_of_business_or_valuation_conclusive_stays_high(self):
        result = calculate_conviction(**_BASE_KWARGS, business_conclusive=True, valuation_conclusive=False)
        assert result.level is ConvictionLevel.HIGH


class TestReasonsAreFixedOrder:
    def test_base_reasons_are_always_coverage_then_contradiction_then_risk_then_staleness_then_open_questions(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.reasons[:5] == (
            ConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
            ConvictionReasonCode.NO_CONTRADICTING_EVIDENCE,
            ConvictionReasonCode.NO_HIGH_FINANCIAL_OR_VALUATION_RISK,
            ConvictionReasonCode.THESIS_NOT_STALE,
            ConvictionReasonCode.NO_OPEN_QUESTIONS,
        )


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_assessment(self):
        first = calculate_conviction(**_BASE_KWARGS)
        second = calculate_conviction(**_BASE_KWARGS)
        assert first == second


class TestNoNumericScore:
    def test_conviction_level_is_a_string_enum_never_a_number(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert isinstance(result.level.value, str)
        assert not hasattr(result, "score")
        assert not hasattr(result, "weight")


class TestStaticValidation:
    """ATLAS-026 Phase 13: prevent reintroducing weighted scoring,
    arithmetic averaging, or undocumented magic constants into
    `conviction.py` specifically -- complements the repository-wide
    `test_no_scoring_patterns_anywhere_in_the_package` in
    `tests/unit/analysis_engine/test_boundaries.py`, which already
    covers this file as part of the whole package."""

    _FORBIDDEN_PATTERNS = (
        "score +=",
        "score -=",
        "weighted_score",
        "weighted score",
        "conviction_score",
        "risk_score",
        " * 0.",
        " * 1.",
        "sum(",
        "/ len(",
        "average",
        "np.mean",
        "statistics.mean",
    )

    def test_source_contains_no_scoring_or_averaging_patterns(self):
        import inspect

        from atlas import analysis_engine

        source = inspect.getsource(analysis_engine.conviction)
        violations = [needle for needle in self._FORBIDDEN_PATTERNS if needle in source]
        assert not violations, f"Forbidden pattern(s) found in conviction.py: {violations}"

    def test_no_numeric_literal_thresholds_in_source(self):
        """Every real branch condition is a named enum comparison
        (`is`, `in`, boolean flags) -- no bare numeric magic constant
        (a percentage, a cutoff) drives any outcome."""
        import inspect
        import re

        from atlas import analysis_engine

        source = inspect.getsource(analysis_engine.conviction)
        # Strip docstrings/comments (which legitimately discuss the
        # concept of thresholds in prose) before scanning real code.
        code_lines = [
            line for line in source.splitlines() if not line.strip().startswith(("#", '"""', "'''"))
        ]
        code_only = "\n".join(code_lines)
        assert not re.search(r"[<>]=?\s*\d", code_only), "Found a numeric comparison threshold in conviction.py"

