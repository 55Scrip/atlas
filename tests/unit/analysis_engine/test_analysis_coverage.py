"""`calculate_analysis_coverage` tests (Internal Alpha Fix Sprint 1,
Part 2 -- confirmed root cause IA-003).

Pure function, no fixtures beyond the three boolean inputs themselves --
mirrors `test_conviction.py`'s own style for `calculate_conviction`.
"""
from __future__ import annotations

from atlas.analysis_engine.analysis_coverage import (
    AnalysisCoverageLevel,
    AnalysisCoverageReasonCode,
    calculate_analysis_coverage,
)


class TestNoCompanyData:
    def test_no_data_is_no_coverage_regardless_of_the_other_signals(self):
        assessment = calculate_analysis_coverage(
            has_company_data=False, business_conclusive=True, valuation_conclusive=True
        )
        assert assessment.level is AnalysisCoverageLevel.NO_COVERAGE
        assert assessment.reasons == (AnalysisCoverageReasonCode.NO_COMPANY_DATA,)

    def test_no_data_and_both_signals_false_is_still_just_no_coverage(self):
        assessment = calculate_analysis_coverage(
            has_company_data=False, business_conclusive=False, valuation_conclusive=False
        )
        assert assessment.level is AnalysisCoverageLevel.NO_COVERAGE
        assert assessment.reasons == (AnalysisCoverageReasonCode.NO_COMPANY_DATA,)


class TestPartialCoverage:
    def test_data_present_but_neither_signal_conclusive_is_partial(self):
        assessment = calculate_analysis_coverage(
            has_company_data=True, business_conclusive=False, valuation_conclusive=False
        )
        assert assessment.level is AnalysisCoverageLevel.PARTIAL_COVERAGE
        assert assessment.reasons == (
            AnalysisCoverageReasonCode.HAS_COMPANY_DATA,
            AnalysisCoverageReasonCode.BUSINESS_ANALYSIS_NOT_YET_CONCLUSIVE,
            AnalysisCoverageReasonCode.VALUATION_NOT_YET_CONCLUSIVE,
        )

    def test_data_present_with_only_business_conclusive_is_partial(self):
        assessment = calculate_analysis_coverage(
            has_company_data=True, business_conclusive=True, valuation_conclusive=False
        )
        assert assessment.level is AnalysisCoverageLevel.PARTIAL_COVERAGE
        assert AnalysisCoverageReasonCode.BUSINESS_ANALYSIS_CONCLUSIVE in assessment.reasons
        assert AnalysisCoverageReasonCode.VALUATION_NOT_YET_CONCLUSIVE in assessment.reasons

    def test_data_present_with_only_valuation_conclusive_is_partial(self):
        assessment = calculate_analysis_coverage(
            has_company_data=True, business_conclusive=False, valuation_conclusive=True
        )
        assert assessment.level is AnalysisCoverageLevel.PARTIAL_COVERAGE
        assert AnalysisCoverageReasonCode.BUSINESS_ANALYSIS_NOT_YET_CONCLUSIVE in assessment.reasons
        assert AnalysisCoverageReasonCode.VALUATION_CONCLUSIVE in assessment.reasons


class TestSubstantialCoverage:
    def test_both_signals_conclusive_is_substantial(self):
        assessment = calculate_analysis_coverage(
            has_company_data=True, business_conclusive=True, valuation_conclusive=True
        )
        assert assessment.level is AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE
        assert assessment.reasons == (
            AnalysisCoverageReasonCode.HAS_COMPANY_DATA,
            AnalysisCoverageReasonCode.BUSINESS_ANALYSIS_CONCLUSIVE,
            AnalysisCoverageReasonCode.VALUATION_CONCLUSIVE,
        )


class TestNeverReadsInvestorEvidence:
    """The whole point of this module: it takes no evidence-coverage
    parameter at all, so it is structurally impossible for it to read
    investor-recorded Observations -- proven by the function's own
    signature accepting only company-data-driven booleans."""

    def test_signature_has_no_evidence_or_confidence_parameter(self):
        import inspect

        params = set(inspect.signature(calculate_analysis_coverage).parameters)
        assert params == {"has_company_data", "business_conclusive", "valuation_conclusive"}
        assert "evidence_coverage" not in params
        assert "confidence" not in params


class TestDeterminism:
    def test_identical_inputs_always_produce_an_identical_assessment(self):
        for has_data, business, valuation in (
            (True, True, True),
            (True, True, False),
            (True, False, True),
            (True, False, False),
            (False, True, True),
            (False, False, False),
        ):
            first = calculate_analysis_coverage(
                has_company_data=has_data, business_conclusive=business, valuation_conclusive=valuation
            )
            second = calculate_analysis_coverage(
                has_company_data=has_data, business_conclusive=business, valuation_conclusive=valuation
            )
            assert first == second
