"""Tests for `atlas.analysis_engine.risk.contracts` (ATLAS-025 Phase 4/5)."""
from __future__ import annotations

from atlas.analysis_engine.findings import FindingSeverity
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus, severity_for_risk_status


class TestRiskStatus:
    def test_exactly_five_members(self):
        assert len(RiskStatus) == 5

    def test_is_a_closed_string_enum(self):
        assert issubclass(RiskStatus, str)
        for member in RiskStatus:
            assert isinstance(member.value, str)

    def test_no_numeric_member(self):
        for member in RiskStatus:
            assert not member.value.isdigit()


class TestRiskDataGapKind:
    def test_every_v1_evaluator_has_a_named_gap_reason(self):
        expected = {
            "growth_assessment_unavailable",
            "capital_allocation_assessment_unavailable",
            "missing_cash_flow_level",
            "valuation_assessment_unavailable",
            "no_evidence_to_evaluate",
        }
        assert {member.value for member in RiskDataGapKind} == expected


class TestSeverityForRiskStatus:
    def test_not_evaluated_and_insufficient_input_are_attention(self):
        assert severity_for_risk_status(RiskStatus.NOT_EVALUATED) is FindingSeverity.ATTENTION
        assert severity_for_risk_status(RiskStatus.INSUFFICIENT_INPUT) is FindingSeverity.ATTENTION

    def test_high_is_material(self):
        assert severity_for_risk_status(RiskStatus.HIGH) is FindingSeverity.MATERIAL

    def test_low_and_moderate_are_info(self):
        assert severity_for_risk_status(RiskStatus.LOW) is FindingSeverity.INFO
        assert severity_for_risk_status(RiskStatus.MODERATE) is FindingSeverity.INFO

    def test_deterministic(self):
        for member in RiskStatus:
            assert severity_for_risk_status(member) == severity_for_risk_status(member)
