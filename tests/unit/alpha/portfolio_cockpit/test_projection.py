"""Tests for `atlas.alpha.portfolio_cockpit.projection` (ATLAS-028 Phase
4/6/7/8) -- pure narrowing functions from real analysis-engine result
objects onto Portfolio Cockpit's compact per-holding types. Every
assertion here proves a *projection*, never a recomputation: the values
returned are always object-identical to (or a direct field copy of) the
real finding they came from."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.portfolio_cockpit.projection import business_summary, risk_projection, valuation_finding
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.risk.contracts import RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskAnalysisResult, RiskFinding
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel
from tests.unit.analysis_engine.risk._fixtures import business_analysis_result, valuation_engine_result

_EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def _prov() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
        consumers=(),
        computed_at=_EVALUATED_AT,
    )


def _risk_finding(category: RiskCategory, status: RiskStatus) -> RiskFinding:
    return RiskFinding(
        id=f"risk_finding:{category.value}",
        category=category,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=(),
        contradicting_facts=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=_prov(),
        evaluated_at=_EVALUATED_AT,
    )


def _risk_analysis(statuses: dict[RiskCategory, RiskStatus]) -> RiskAnalysisResult:
    assert set(statuses) == EVALUATED_RISK_CATEGORIES
    return RiskAnalysisResult(
        state=EvaluationState.EVALUATED,
        findings=tuple(_risk_finding(category, status) for category, status in statuses.items()),
    )


class TestBusinessSummary:
    def test_narrows_to_growth_and_capital_allocation_only(self):
        analysis = business_analysis_result(
            growth=BusinessCategoryStatus.STRONG, capital_allocation=BusinessCategoryStatus.WEAK
        )
        summary = business_summary(analysis)
        assert summary.growth is BusinessCategoryStatus.STRONG
        assert summary.capital_allocation is BusinessCategoryStatus.WEAK

    def test_never_a_synthesized_six_category_aggregate(self):
        summary = business_summary(
            business_analysis_result(
                growth=BusinessCategoryStatus.INSUFFICIENT_INPUT,
                capital_allocation=BusinessCategoryStatus.INSUFFICIENT_INPUT,
            )
        )
        assert set(summary.__dataclass_fields__) == {"growth", "capital_allocation"}


class TestValuationFinding:
    def test_returns_the_real_fcf_yield_relative_finding_by_identity(self):
        engine_result = valuation_engine_result(fcf_yield=ValuationStatus.EXPENSIVE)
        expected = next(f for f in engine_result.findings if f.kind.value == "fcf_yield_relative")
        assert valuation_finding(engine_result) is expected


class TestRiskProjectionSeverityOrdering:
    def test_high_beats_moderate_low_and_insufficient(self):
        analysis = _risk_analysis(
            {
                RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                RiskCategory.FINANCIAL_RISK: RiskStatus.HIGH,
                RiskCategory.THESIS_RISK: RiskStatus.MODERATE,
                RiskCategory.VALUATION_RISK: RiskStatus.INSUFFICIENT_INPUT,
            }
        )
        projection = risk_projection(analysis)
        assert projection.category is RiskCategory.FINANCIAL_RISK
        assert projection.status is RiskStatus.HIGH

    def test_moderate_beats_low(self):
        analysis = _risk_analysis(
            {
                RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                RiskCategory.FINANCIAL_RISK: RiskStatus.LOW,
                RiskCategory.THESIS_RISK: RiskStatus.MODERATE,
                RiskCategory.VALUATION_RISK: RiskStatus.LOW,
            }
        )
        assert risk_projection(analysis).category is RiskCategory.THESIS_RISK


class TestRiskProjectionTieBreaking:
    """Confirmed rule: ties broken by `RiskCategory`'s own declared enum
    order -- BUSINESS_RISK, FINANCIAL_RISK, THESIS_RISK, VALUATION_RISK
    among the four evaluated categories -- never an invented priority."""

    def test_all_tied_at_insufficient_input_picks_business_risk_first(self):
        analysis = _risk_analysis({c: RiskStatus.INSUFFICIENT_INPUT for c in EVALUATED_RISK_CATEGORIES})
        assert risk_projection(analysis).category is RiskCategory.BUSINESS_RISK

    def test_all_tied_at_high_still_picks_business_risk_first(self):
        analysis = _risk_analysis({c: RiskStatus.HIGH for c in EVALUATED_RISK_CATEGORIES})
        assert risk_projection(analysis).category is RiskCategory.BUSINESS_RISK
        assert risk_projection(analysis).status is RiskStatus.HIGH

    def test_financial_beats_thesis_and_valuation_when_tied(self):
        analysis = _risk_analysis(
            {
                RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                RiskCategory.FINANCIAL_RISK: RiskStatus.HIGH,
                RiskCategory.THESIS_RISK: RiskStatus.HIGH,
                RiskCategory.VALUATION_RISK: RiskStatus.HIGH,
            }
        )
        assert risk_projection(analysis).category is RiskCategory.FINANCIAL_RISK

    def test_thesis_beats_valuation_when_tied(self):
        analysis = _risk_analysis(
            {
                RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                RiskCategory.FINANCIAL_RISK: RiskStatus.LOW,
                RiskCategory.THESIS_RISK: RiskStatus.HIGH,
                RiskCategory.VALUATION_RISK: RiskStatus.HIGH,
            }
        )
        assert risk_projection(analysis).category is RiskCategory.THESIS_RISK


class TestRiskProjectionIsNeverAnAverage:
    def test_result_is_exactly_one_categorys_own_real_status(self):
        analysis = _risk_analysis(
            {
                RiskCategory.BUSINESS_RISK: RiskStatus.LOW,
                RiskCategory.FINANCIAL_RISK: RiskStatus.HIGH,
                RiskCategory.THESIS_RISK: RiskStatus.MODERATE,
                RiskCategory.VALUATION_RISK: RiskStatus.INSUFFICIENT_INPUT,
            }
        )
        expected = next(f for f in analysis.findings if f.category is RiskCategory.FINANCIAL_RISK)
        projection = risk_projection(analysis)
        assert projection.category is expected.category
        assert projection.status is expected.status
