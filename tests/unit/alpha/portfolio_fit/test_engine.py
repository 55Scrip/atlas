"""Pure unit tests for `atlas.alpha.portfolio_fit.engine` -- the
deterministic decision-table functions each Portfolio Fit dimension uses.
Every fixture below is the smallest valid instance of its type; this
file never goes through the real analysis pipeline (that is covered by
`tests/unit/alpha/portfolio_fit/test_service.py`'s real-persistence
harness instead, mirroring `tests/unit/alpha/daily_brief/test_service.py`'s
own division of labor).
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.coverage import ConfidenceLevel, CoverageAssessment
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.alpha.portfolio_fit.engine import (
    _allocation_fit,
    _business_fit,
    _cash_impact_fit,
    _expected_contribution_fit,
    _overall_fit,
    _risk_fit,
    _valuation_fit,
    compare_fit,
)
from atlas.alpha.portfolio_fit.models import (
    FitDimension,
    FitDimensionKind,
    FitRating,
    FitTrend,
    FitVerdictReasonCode,
    PortfolioFitAssessment,
)
from atlas.analysis_engine.business_contracts import (
    BusinessAnalysisResult,
    BusinessCategory,
    BusinessCategoryStatus,
    BusinessFinding,
)
from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.outlook import (
    ExpectedReturnRange,
    HorizonOutlook,
    OutlookAssumption,
    OutlookAssumptionKind,
    OutlookGapKind,
    OutlookHorizon,
    OutlookMomentumKind,
    ReturnBasis,
)
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskStatus
from atlas.analysis_engine.risk.models import RiskAnalysisResult, RiskFinding
from atlas.analysis_engine.valuation.models import ValuationEngineResult, ValuationFinding
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupport, ValuationSupportGapKind, ValuationSupportStatus
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _provenance() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
        consumers=(Consumer.INVESTMENT_CASE_PAGE,),
        computed_at=_NOW,
    )


def _business_finding(category: BusinessCategory, status: BusinessCategoryStatus) -> BusinessFinding:
    return BusinessFinding(
        id=f"business-{category.value}",
        kind=category,
        status=status,
        severity=FindingSeverity.INFO,
        supporting_evidence=(),
        contradicting_evidence=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_provenance(),
        updated_at=_NOW,
    )


def _business_analysis(statuses: dict[BusinessCategory, BusinessCategoryStatus]) -> BusinessAnalysisResult:
    return BusinessAnalysisResult(
        state=EvaluationState.EVALUATED,
        findings=tuple(_business_finding(category, status) for category, status in statuses.items()),
    )


def _all_business_categories(status: BusinessCategoryStatus, *, overrides: dict[BusinessCategory, BusinessCategoryStatus] | None = None) -> BusinessAnalysisResult:
    statuses = {category: status for category in BusinessCategory}
    statuses.update(overrides or {})
    return _business_analysis(statuses)


def _risk_finding(category: RiskCategory, status: RiskStatus) -> RiskFinding:
    return RiskFinding(
        id=f"risk-{category.value}",
        category=category,
        status=status,
        severity=FindingSeverity.INFO,
        supporting_facts=(),
        contradicting_facts=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_provenance(),
        evaluated_at=_NOW,
    )


_EVALUATED_RISK_CATEGORIES = (RiskCategory.BUSINESS_RISK, RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK, RiskCategory.THESIS_RISK)


def _risk_analysis(status: RiskStatus, *, overrides: dict[RiskCategory, RiskStatus] | None = None) -> RiskAnalysisResult:
    statuses = {category: status for category in _EVALUATED_RISK_CATEGORIES}
    statuses.update(overrides or {})
    return RiskAnalysisResult(
        state=EvaluationState.EVALUATED,
        findings=tuple(_risk_finding(category, s) for category, s in statuses.items()),
    )


def _valuation_finding(kind: ValuationMethodKind, status: ValuationStatus) -> ValuationFinding:
    return ValuationFinding(
        id=f"valuation-{kind.value}",
        kind=kind,
        status=status,
        severity=FindingSeverity.INFO,
        supporting_facts=(),
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_provenance(),
        evaluated_at=_NOW,
    )


def _valuation_engine(status: ValuationStatus) -> ValuationEngineResult:
    # An EVALUATED `ValuationEngineResult` must carry a finding for every
    # `ValuationMethodKind` member (own `__post_init__` contract) -- the
    # three `SCENARIO_*` kinds are permanently `INSUFFICIENT_INPUT` in
    # this codebase today (confirmed via `valuation/contracts.py`'s own
    # docstring), so only `FCF_YIELD_RELATIVE` varies here.
    findings = [_valuation_finding(ValuationMethodKind.FCF_YIELD_RELATIVE, status)]
    for kind in ValuationMethodKind:
        if kind is not ValuationMethodKind.FCF_YIELD_RELATIVE:
            findings.append(_valuation_finding(kind, ValuationStatus.INSUFFICIENT_INPUT))
    return ValuationEngineResult(state=EvaluationState.EVALUATED, findings=tuple(findings))


def _valuation_support(status: ValuationSupportStatus) -> ValuationSupport:
    gap = ValuationSupportGapKind.NO_SUFFICIENT_VALUATION_PROOF if status is ValuationSupportStatus.INSUFFICIENT_INPUT else None
    return ValuationSupport(status=status, reasoning="test", gap=gap)


def _outlook_assumption() -> OutlookAssumption:
    return OutlookAssumption(
        kind=OutlookAssumptionKind.HISTORICAL_FCF_YIELD_REVERSION,
        current_fcf_yield=0.05,
        target_fcf_yield=0.05,
        observation_count=4,
    )


def _horizon_outlook(low_percent: float | None, high_percent: float | None) -> HorizonOutlook:
    expected_return = (
        ExpectedReturnRange(
            low_percent=low_percent,
            high_percent=high_percent,
            basis=ReturnBasis.ANNUALIZED,
            horizon_months_low=24,
            horizon_months_high=36,
            assumption=_outlook_assumption(),
        )
        if low_percent is not None
        else None
    )
    return HorizonOutlook(
        horizon=OutlookHorizon.LONG_TERM,
        expected_return=expected_return,
        expected_return_gap=None if expected_return is not None else OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE,
        scenarios=(),
        scenarios_gap=OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE,
        conviction=ConvictionLevel.MODERATE,
        momentum=OutlookMomentumKind.UNAVAILABLE,
        key_drivers=(),
    )


def _portfolio_state(*, holdings: tuple[AlphaHolding, ...] = (), cash_weight_percent: float | None = None) -> AlphaPortfolioState:
    return AlphaPortfolioState(
        established_at=_NOW,
        updated_at=_NOW,
        entry_mode=EntryMode.FROM_SCRATCH,
        holdings=holdings,
        cash_weight_percent=cash_weight_percent,
    )


class TestBusinessFit:
    def test_all_strong_is_excellent(self):
        result = _business_fit(_all_business_categories(BusinessCategoryStatus.STRONG))
        assert result.rating is FitRating.EXCELLENT

    def test_all_weak_is_poor(self):
        result = _business_fit(_all_business_categories(BusinessCategoryStatus.WEAK))
        assert result.rating is FitRating.POOR

    def test_not_evaluated_state_is_unavailable(self):
        result = _business_fit(BusinessAnalysisResult(state=EvaluationState.NOT_EVALUATED, findings=()))
        assert result.rating is FitRating.UNAVAILABLE
        assert result.unavailable_reason is not None

    def test_same_input_produces_same_rating_every_time(self):
        analysis = _all_business_categories(BusinessCategoryStatus.MODERATE)
        first = _business_fit(analysis)
        second = _business_fit(analysis)
        assert first == second


class TestValuationFit:
    def test_undervalued_and_supported_is_excellent(self):
        result = _valuation_fit(_valuation_engine(ValuationStatus.UNDERVALUED), _valuation_support(ValuationSupportStatus.SUPPORTED))
        assert result.rating is FitRating.EXCELLENT

    def test_expensive_and_not_supported_is_poor(self):
        result = _valuation_fit(_valuation_engine(ValuationStatus.EXPENSIVE), _valuation_support(ValuationSupportStatus.NOT_SUPPORTED))
        assert result.rating is FitRating.POOR

    def test_no_conclusive_data_at_all_is_unavailable(self):
        engine_result = ValuationEngineResult(state=EvaluationState.INSUFFICIENT_INPUT, findings=())
        result = _valuation_fit(engine_result, _valuation_support(ValuationSupportStatus.INSUFFICIENT_INPUT))
        assert result.rating is FitRating.UNAVAILABLE


class TestRiskFit:
    def test_all_low_is_excellent(self):
        result = _risk_fit(_risk_analysis(RiskStatus.LOW))
        assert result.rating is FitRating.EXCELLENT

    def test_two_high_is_poor(self):
        result = _risk_fit(_risk_analysis(RiskStatus.LOW, overrides={
            RiskCategory.FINANCIAL_RISK: RiskStatus.HIGH,
            RiskCategory.VALUATION_RISK: RiskStatus.HIGH,
        }))
        assert result.rating is FitRating.POOR

    def test_one_high_is_weak(self):
        result = _risk_fit(_risk_analysis(RiskStatus.LOW, overrides={RiskCategory.FINANCIAL_RISK: RiskStatus.HIGH}))
        assert result.rating is FitRating.WEAK

    def test_not_evaluated_is_unavailable(self):
        result = _risk_fit(RiskAnalysisResult(state=EvaluationState.NOT_EVALUATED, findings=()))
        assert result.rating is FitRating.UNAVAILABLE


class TestAllocationFit:
    def test_existing_holding_above_high_threshold_is_poor(self):
        holding = AlphaHolding(ticker="AAPL", weight_percent=40.0)
        result = _allocation_fit(holding, _portfolio_state(holdings=(holding,)))
        assert result.rating is FitRating.POOR

    def test_existing_holding_small_weight_is_excellent(self):
        holding = AlphaHolding(ticker="AAPL", weight_percent=2.0)
        result = _allocation_fit(holding, _portfolio_state(holdings=(holding,)))
        assert result.rating is FitRating.EXCELLENT

    def test_candidate_with_no_holding_never_reaches_excellent(self):
        result = _allocation_fit(None, _portfolio_state())
        assert result.rating is not FitRating.EXCELLENT
        assert result.rating is not FitRating.UNAVAILABLE


class TestExpectedContributionFit:
    def test_high_positive_range_is_excellent(self):
        result = _expected_contribution_fit(_horizon_outlook(0.12, 0.25))
        assert result.rating is FitRating.EXCELLENT

    def test_deeply_negative_low_bound_is_poor(self):
        result = _expected_contribution_fit(_horizon_outlook(-0.20, -0.05))
        assert result.rating is FitRating.POOR

    def test_no_range_available_is_unavailable(self):
        result = _expected_contribution_fit(_horizon_outlook(None, None))
        assert result.rating is FitRating.UNAVAILABLE
        assert result.unavailable_reason is not None


class TestCashImpactFit:
    def test_ample_cash_is_excellent(self):
        result = _cash_impact_fit(_portfolio_state(cash_weight_percent=20.0))
        assert result.rating is FitRating.EXCELLENT

    def test_negligible_cash_is_poor(self):
        result = _cash_impact_fit(_portfolio_state(cash_weight_percent=0.2))
        assert result.rating is FitRating.POOR

    def test_no_cash_recorded_is_unavailable(self):
        result = _cash_impact_fit(_portfolio_state(cash_weight_percent=None))
        assert result.rating is FitRating.UNAVAILABLE


def _dim(kind: FitDimensionKind, rating: FitRating) -> FitDimension:
    return FitDimension(kind=kind, rating=rating, reasoning=())


class TestOverallFit:
    def test_all_excellent_is_excellent(self):
        dims = tuple(_dim(kind, FitRating.EXCELLENT) for kind in FitDimensionKind)
        overall, _, code, count = _overall_fit(dims)
        assert overall is FitRating.EXCELLENT
        assert code is FitVerdictReasonCode.MOSTLY_EXCELLENT
        assert count == len(FitDimensionKind)

    def test_poor_risk_gates_the_overall_verdict_even_with_other_dimensions_excellent(self):
        dims = tuple(
            _dim(kind, FitRating.POOR if kind is FitDimensionKind.RISK else FitRating.EXCELLENT)
            for kind in FitDimensionKind
        )
        overall, reasoning, code, count = _overall_fit(dims)
        assert overall is FitRating.POOR
        assert any("Risk Fit" in r for r in reasoning)
        assert code is FitVerdictReasonCode.RISK_GATE
        assert count is None

    def test_all_unavailable_is_unavailable(self):
        dims = tuple(_dim(kind, FitRating.UNAVAILABLE) for kind in FitDimensionKind)
        overall, _, code, _count = _overall_fit(dims)
        assert overall is FitRating.UNAVAILABLE
        assert code is FitVerdictReasonCode.NO_DIMENSION_EVALUATED

    def test_same_dimension_set_always_produces_same_overall(self):
        dims = (
            _dim(FitDimensionKind.BUSINESS, FitRating.GOOD),
            _dim(FitDimensionKind.VALUATION, FitRating.NEUTRAL),
            _dim(FitDimensionKind.RISK, FitRating.GOOD),
        )
        first, _, _, _ = _overall_fit(dims)
        second, _, _, _ = _overall_fit(dims)
        assert first == second


_EMPTY_COVERAGE = CoverageAssessment(
    dimensions=(),
    overall_coverage=AnalysisCoverageLevel.NO_COVERAGE,
    overall_confidence=ConfidenceLevel.VERY_LIMITED,
    missing_dimensions=(),
    not_applicable_dimensions=(),
    reasoning=("No company data available.",),
)


def _assessment(ticker: str, overall: FitRating, dimensions: tuple[FitDimension, ...] = ()) -> PortfolioFitAssessment:
    return PortfolioFitAssessment(
        case_id=f"case-{ticker.lower()}",
        ticker=ticker,
        is_existing_holding=False,
        current_weight_percent=None,
        overall=overall,
        overall_reasoning=(),
        overall_reasoning_code=None,
        overall_reasoning_count=None,
        dimensions=dimensions,
        trend=FitTrend.UNAVAILABLE,
        data_gaps=(),
        coverage=_EMPTY_COVERAGE,
        generated_at=_NOW,
    )


class TestCompareFit:
    """Product Sprint 5 (Discovery Engine v2), Deliverable 13 -- `compare_fit`
    (Product Sprint 4) had no direct unit test of its own tie-handling
    before this sprint; only `test_service.py`'s integration test
    exercised it, with real, differently-rated Cases that never actually
    tied. Added here to close that real gap, found during this sprint's
    own test-coverage audit."""

    def test_equal_overall_ratings_produce_a_tie_never_a_forced_winner(self):
        comparison = compare_fit(_assessment("AAPL", FitRating.GOOD), _assessment("MSFT", FitRating.GOOD))
        assert comparison.preferred_ticker is None
        assert "Good" in comparison.reasoning[0]

    def test_both_unavailable_is_also_a_disclosed_tie(self):
        comparison = compare_fit(_assessment("AAPL", FitRating.UNAVAILABLE), _assessment("MSFT", FitRating.UNAVAILABLE))
        assert comparison.preferred_ticker is None

    def test_a_higher_rated_candidate_is_preferred(self):
        comparison = compare_fit(_assessment("AAPL", FitRating.EXCELLENT), _assessment("MSFT", FitRating.WEAK))
        assert comparison.preferred_ticker == "AAPL"

    def test_preference_is_symmetric_regardless_of_argument_order(self):
        a = compare_fit(_assessment("AAPL", FitRating.EXCELLENT), _assessment("MSFT", FitRating.WEAK))
        b = compare_fit(_assessment("MSFT", FitRating.WEAK), _assessment("AAPL", FitRating.EXCELLENT))
        assert a.preferred_ticker == b.preferred_ticker == "AAPL"

    def test_reasoning_names_which_dimension_differs_between_the_two(self):
        comparison = compare_fit(
            _assessment("AAPL", FitRating.GOOD, (_dim(FitDimensionKind.RISK, FitRating.GOOD),)),
            _assessment("MSFT", FitRating.WEAK, (_dim(FitDimensionKind.RISK, FitRating.POOR),)),
        )
        assert comparison.preferred_ticker == "AAPL"
        assert any("Risk" in line for line in comparison.reasoning)

    def test_compare_computes_nothing_new_about_either_assessment(self):
        """Reads the two already-computed assessments verbatim -- never
        recomputes a dimension or an overall rating of its own."""
        a = _assessment("AAPL", FitRating.GOOD)
        b = _assessment("MSFT", FitRating.WEAK)
        comparison = compare_fit(a, b)
        assert comparison.assessment_a is a
        assert comparison.assessment_b is b
