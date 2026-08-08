"""Tests for `atlas.analysis_engine.risk.models` (ATLAS-025 Phase 4/13)."""
from __future__ import annotations

import pytest

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.risk.contracts import RiskStatus, severity_for_risk_status
from atlas.analysis_engine.risk.models import EVALUATED_RISK_CATEGORIES, RiskAnalysisResult, RiskFinding
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.risk._fixtures import EVALUATED_AT, EvaluationState


def _risk_finding(category: RiskCategory, status: RiskStatus = RiskStatus.LOW) -> RiskFinding:
    from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger

    return RiskFinding(
        id=f"risk_finding:{category.value}",
        category=category,
        status=status,
        severity=severity_for_risk_status(status),
        supporting_facts=(),
        contradicting_facts=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.FULL,
        provenance=Provenance(
            source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
            source_references=(),
            dependencies=(),
            update_trigger=UpdateTrigger.UPSTREAM_STAGE_CHANGED,
            consumers=(),
            computed_at=EVALUATED_AT,
        ),
        evaluated_at=EVALUATED_AT,
    )


class TestEvaluatedRiskCategories:
    def test_exactly_four_v1_categories(self):
        assert EVALUATED_RISK_CATEGORIES == {
            RiskCategory.BUSINESS_RISK,
            RiskCategory.FINANCIAL_RISK,
            RiskCategory.VALUATION_RISK,
            RiskCategory.THESIS_RISK,
        }

    def test_is_a_proper_subset_of_the_full_taxonomy(self):
        assert EVALUATED_RISK_CATEGORIES < set(RiskCategory)


class TestRiskAnalysisResultInvariant:
    def test_evaluated_with_exactly_the_four_categories_is_valid(self):
        findings = tuple(_risk_finding(category) for category in EVALUATED_RISK_CATEGORIES)
        result = RiskAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)
        assert {f.category for f in result.findings} == EVALUATED_RISK_CATEGORIES

    def test_evaluated_missing_a_category_raises(self):
        findings = tuple(
            _risk_finding(category) for category in EVALUATED_RISK_CATEGORIES if category is not RiskCategory.THESIS_RISK
        )
        with pytest.raises(AnalysisEngineContractError):
            RiskAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)

    def test_evaluated_with_an_unexpected_extra_category_raises(self):
        findings = tuple(_risk_finding(category) for category in EVALUATED_RISK_CATEGORIES) + (
            _risk_finding(RiskCategory.PORTFOLIO_RISK),
        )
        with pytest.raises(AnalysisEngineContractError):
            RiskAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)


class TestNoAggregateLabel:
    def test_result_has_no_overall_status_field(self):
        findings = tuple(_risk_finding(category) for category in EVALUATED_RISK_CATEGORIES)
        result = RiskAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)
        assert not hasattr(result, "overall_status")
        assert not hasattr(result, "score")
        assert not hasattr(result, "risk_score")
