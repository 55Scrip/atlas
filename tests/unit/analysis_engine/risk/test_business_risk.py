"""Tests for `atlas.analysis_engine.risk.business_risk.evaluate_business_risk`
(ATLAS-025 Phase 7) -- the documented rule table and edge cases."""
from __future__ import annotations

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.business_risk import evaluate_business_risk
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.risk._fixtures import EVALUATED_AT, growth_finding


class TestRuleTable:
    def test_insufficient_input_growth_is_insufficient_input_risk(self):
        finding = growth_finding(BusinessCategoryStatus.INSUFFICIENT_INPUT)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.INSUFFICIENT_INPUT
        assert RiskDataGapKind.GROWTH_ASSESSMENT_UNAVAILABLE in result.missing_evidence

    def test_weak_growth_is_high_risk(self):
        finding = growth_finding(BusinessCategoryStatus.WEAK)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.HIGH

    def test_moderate_growth_is_moderate_risk(self):
        finding = growth_finding(BusinessCategoryStatus.MODERATE)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.MODERATE

    def test_strong_growth_is_low_risk(self):
        finding = growth_finding(BusinessCategoryStatus.STRONG)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is RiskStatus.LOW


class TestMissingIsNotRisk:
    def test_insufficient_input_never_maps_to_high(self):
        """Phase 7's own critical rule: uncertainty must never be
        silently converted into a negative risk conclusion."""
        finding = growth_finding(BusinessCategoryStatus.INSUFFICIENT_INPUT)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.status is not RiskStatus.HIGH
        assert result.status is not RiskStatus.MODERATE
        assert result.status is not RiskStatus.LOW


class TestTraceability:
    def test_category_and_id_are_correct(self):
        finding = growth_finding(BusinessCategoryStatus.STRONG)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.category is RiskCategory.BUSINESS_RISK
        assert result.id == "risk_finding:business_risk"

    def test_growth_finding_id_is_a_supporting_fact_and_dependency(self):
        finding = growth_finding(BusinessCategoryStatus.STRONG)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert finding.id in result.supporting_facts
        assert finding.id in result.provenance.dependencies

    def test_confidence_reuses_growth_findings_confidence_verbatim(self):
        finding = growth_finding(BusinessCategoryStatus.MODERATE, confidence=EvidenceCoverageLevel.PARTIAL)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.confidence is EvidenceCoverageLevel.PARTIAL

    def test_never_reads_contradicting_evidence(self):
        """This evaluator has no contradicting-evidence input at all --
        that signal belongs exclusively to Thesis Risk."""
        finding = growth_finding(BusinessCategoryStatus.WEAK)
        result = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert result.contradicting_facts == ()


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_finding(self):
        finding = growth_finding(BusinessCategoryStatus.MODERATE)
        first = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        second = evaluate_business_risk(finding, evaluated_at=EVALUATED_AT)
        assert first == second
