"""Decision-table coverage for `atlas.analysis_engine.conviction
.calculate_conviction` (ATLAS-020 Phase 9; extended ATLAS-026 Phase 4;
redesigned Calibration Phase 4 -- Conviction & Capital Allocation
Repair) -- every branch of the ordered if/elif chain, exercised
directly against its own inputs rather than through the full pipeline,
so each branch is isolated.

Calibration Phase 4: `evidence_coverage: EvidenceCoverageLevel`
(investor-Observation-based) was replaced by `analysis_coverage:
AnalysisCoverageLevel` (Atlas's own company-data-based knowledge), used
now only for the `NO_COVERAGE` floor -- `business_conclusive`/
`valuation_conclusive` (already Atlas's own knowledge, not new) became
the sole signal for both the `LOW` trigger (neither has concluded
anything) and the `HIGH`/`VERY_HIGH` split (exactly one vs. both), since
`AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE` is itself defined as
`business_conclusive and valuation_conclusive` and gating `LOW` on
`PARTIAL_COVERAGE` too would have made `HIGH` unreachable in real
pipeline flow (see `conviction.py`'s own module/function docstrings).
`_BASE_KWARGS` is therefore the "fully conclusive, nothing wrong"
baseline reaching `VERY_HIGH` by default -- each test below overrides
only the one dimension it probes."""
from __future__ import annotations

from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.conviction import (
    ConvictionLevel,
    ConvictionReasonCode,
    calculate_conviction,
)
from atlas.decision_engine.contracts import EvaluationState

_BASE_KWARGS = dict(
    business_state=EvaluationState.EVALUATED,
    valuation_state=EvaluationState.EVALUATED,
    analysis_coverage=AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE,
    business_conclusive=True,
    valuation_conclusive=True,
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


class TestAnalysisCoverageInsufficient:
    """Calibration Phase 4: this is now gated on Atlas's own knowledge
    of the company (real data ingested, real conclusions reached) --
    never on whether the investor has recorded any Observations."""

    def test_no_coverage_yields_insufficient_evidence(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "analysis_coverage": AnalysisCoverageLevel.NO_COVERAGE})
        assert result.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert result.reasons == (ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,)


class TestLowConviction:
    def test_contradicting_evidence_yields_low_regardless_of_coverage(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "has_contradicting_evidence": True})
        assert result.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT in result.reasons

    def test_neither_business_nor_valuation_conclusive_yields_low(self):
        """Real company data exists (`analysis_coverage` is not
        `NO_COVERAGE`) but neither Growth/Capital Allocation nor the
        Valuation method has concluded anything concrete yet -- e.g.
        too little history for a trend classification."""
        result = calculate_conviction(
            **{**_BASE_KWARGS, "business_conclusive": False, "valuation_conclusive": False}
        )
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
        result = calculate_conviction(**{**_BASE_KWARGS, "has_high_financial_or_valuation_risk": True})
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
    def test_exactly_one_of_business_or_valuation_conclusive_yields_high(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "valuation_conclusive": False})
        assert result.level is ConvictionLevel.HIGH
        assert ConvictionReasonCode.BUSINESS_OR_VALUATION_NOT_YET_CONCLUSIVE in result.reasons


class TestVeryHighConviction:
    def test_conclusive_business_and_valuation_yields_very_high(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.level is ConvictionLevel.VERY_HIGH
        assert ConvictionReasonCode.BUSINESS_AND_VALUATION_CONCLUSIVE in result.reasons

    def test_only_one_of_business_or_valuation_conclusive_stays_high(self):
        result = calculate_conviction(**{**_BASE_KWARGS, "valuation_conclusive": False})
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


class TestIndependenceFromUserNotes:
    """Calibration Phase 4's own core deliverable: Conviction must not
    require any investor-recorded Decision/Observation to reach a real,
    non-insufficient level. `_BASE_KWARGS` itself is the proof -- it
    contains no investor-history concept anywhere (no Decision,
    Observation, or Evidence record is constructed or referenced by
    this whole test file) and still reaches every tier from
    `INSUFFICIENT_EVIDENCE` through `VERY_HIGH`, driven only by
    `AnalysisCoverageLevel` (company-data-derived) and Atlas's own
    Business/Valuation/Risk conclusiveness flags."""

    def test_very_high_is_reachable_with_zero_investor_history_concepts_anywhere_in_the_call(self):
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.level is ConvictionLevel.VERY_HIGH

    def test_substantial_analysis_coverage_alone_clears_the_insufficient_evidence_floor(self):
        """The floor question is now "does Atlas have real company data
        and real conclusions," never "has the investor written
        anything" -- confirmed by the fact this call constructs no
        Decision/Observation/Evidence object at all."""
        result = calculate_conviction(**_BASE_KWARGS)
        assert result.level is not ConvictionLevel.INSUFFICIENT_EVIDENCE


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
