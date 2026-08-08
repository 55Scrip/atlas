"""Tests for `atlas.analysis_engine.valuation.scenarios` (ATLAS-024
Phase 8) -- real, tested structure, honestly always
INSUFFICIENT_INPUT this sprint."""
from __future__ import annotations

from atlas.analysis_engine.valuation.contracts import ValuationDataGapKind, ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.scenarios import SCENARIO_METHOD_KINDS, build_scenario_findings
from atlas.decision_engine.contracts import EvidenceCoverageLevel
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT


class TestStructuralCompleteness:
    def test_exactly_three_scenario_findings(self):
        findings = build_scenario_findings(evaluated_at=EVALUATED_AT)
        assert len(findings) == 3
        assert {f.kind for f in findings} == set(SCENARIO_METHOD_KINDS)

    def test_all_three_are_bear_base_bull(self):
        findings = build_scenario_findings(evaluated_at=EVALUATED_AT)
        kinds = {f.kind for f in findings}
        assert kinds == {
            ValuationMethodKind.SCENARIO_BEAR,
            ValuationMethodKind.SCENARIO_BASE,
            ValuationMethodKind.SCENARIO_BULL,
        }


class TestNoFabrication:
    def test_all_scenarios_are_insufficient_input(self):
        findings = build_scenario_findings(evaluated_at=EVALUATED_AT)
        for finding in findings:
            assert finding.status is ValuationStatus.INSUFFICIENT_INPUT

    def test_no_assumptions_are_silently_created(self):
        findings = build_scenario_findings(evaluated_at=EVALUATED_AT)
        for finding in findings:
            assert finding.assumptions == ()
            assert ValuationDataGapKind.MISSING_SCENARIO_ASSUMPTIONS in finding.missing_evidence

    def test_confidence_is_not_applicable(self):
        findings = build_scenario_findings(evaluated_at=EVALUATED_AT)
        for finding in findings:
            assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE


class TestDeterminism:
    def test_identical_calls_produce_identical_findings(self):
        first = build_scenario_findings(evaluated_at=EVALUATED_AT)
        second = build_scenario_findings(evaluated_at=EVALUATED_AT)
        assert first == second
