"""Decision-table coverage for `atlas.analysis_engine.conviction
.calculate_conviction` (ATLAS-020 Phase 9) -- every branch of the
ordered if/elif chain, exercised directly against its own inputs rather
than through the full pipeline, so each branch is isolated."""
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
    def test_full_coverage_no_contradiction_no_staleness_no_open_questions_yields_high(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.level is ConvictionLevel.HIGH
        assert ConvictionReasonCode.BUSINESS_OR_VALUATION_NOT_YET_CONCLUSIVE in result.reasons

    def test_very_high_is_unreachable_under_todays_default_conclusiveness(self):
        """Sprint lock: `business_conclusive`/`valuation_conclusive`
        default `False` because Durability and substantive Valuation are
        both structurally `INSUFFICIENT_INPUT` today -- so the best
        conviction any real caller can honestly reach right now is
        `HIGH`, never `VERY_HIGH`."""
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
    def test_base_reasons_are_always_coverage_then_contradiction_then_staleness_then_open_questions(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.reasons[:4] == (
            ConvictionReasonCode.EVIDENCE_COVERAGE_FULL,
            ConvictionReasonCode.NO_CONTRADICTING_EVIDENCE,
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
