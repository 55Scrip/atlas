"""Tests for `atlas.analysis_engine.risk.thesis_risk.evaluate_thesis_risk`
(ATLAS-025 Phase 9/15) -- the documented rule table, plus proof that the
pre-existing per-observation Findings mechanism is reused, not
recomputed."""
from __future__ import annotations

from atlas.analysis_engine.contracts import RiskCategory
from atlas.analysis_engine.risk.contracts import RiskDataGapKind, RiskStatus
from atlas.analysis_engine.risk.thesis_risk import evaluate_thesis_risk
from atlas.decision_engine.contracts import EvidenceCoverageLevel, ObservationEpistemicStatus
from tests.unit.analysis_engine.risk._fixtures import EVALUATED_AT, classification, contradiction_summary


class TestRuleTable:
    def test_no_evidence_coverage_at_all_is_insufficient_input(self):
        summary = contradiction_summary()
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.NOT_APPLICABLE, evaluated_at=EVALUATED_AT
        )
        assert result.status is RiskStatus.INSUFFICIENT_INPUT
        assert RiskDataGapKind.NO_EVIDENCE_TO_EVALUATE in result.missing_evidence

    def test_evidence_exists_but_none_is_challenged_is_insufficient_input(self):
        """`NONE` coverage means Observations exist but none has any
        Evidence at all -- still nothing to check for contradiction."""
        summary = contradiction_summary()
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.NONE, evaluated_at=EVALUATED_AT
        )
        assert result.status is RiskStatus.INSUFFICIENT_INPUT

    def test_evidence_exists_and_contradicts_is_high(self):
        classified = classification(ObservationEpistemicStatus.CONTRADICTED, challenging_count=2)
        summary = contradiction_summary(classified)
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.PARTIAL, evaluated_at=EVALUATED_AT
        )
        assert result.status is RiskStatus.HIGH
        assert str(classified.observation_id) in result.contradicting_facts

    def test_evidence_exists_and_none_contradicts_is_low(self):
        summary = contradiction_summary()
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.FULL, evaluated_at=EVALUATED_AT
        )
        assert result.status is RiskStatus.LOW

    def test_no_moderate_tier_is_ever_produced(self):
        for coverage in EvidenceCoverageLevel:
            result = evaluate_thesis_risk(contradiction_summary(), evidence_coverage=coverage, evaluated_at=EVALUATED_AT)
            assert result.status is not RiskStatus.MODERATE


class TestMultipleContradictions:
    def test_all_contradicted_observation_ids_are_named(self):
        c1 = classification(ObservationEpistemicStatus.CONTRADICTED, challenging_count=1)
        c2 = classification(ObservationEpistemicStatus.CONTRADICTED, challenging_count=3)
        summary = contradiction_summary(c1, c2)
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.FULL, evaluated_at=EVALUATED_AT
        )
        assert result.status is RiskStatus.HIGH
        assert {str(c1.observation_id), str(c2.observation_id)} == set(result.contradicting_facts)


class TestTraceability:
    def test_category_and_id_are_correct(self):
        summary = contradiction_summary()
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.FULL, evaluated_at=EVALUATED_AT
        )
        assert result.category is RiskCategory.THESIS_RISK
        assert result.id == "risk_finding:thesis_risk"

    def test_confidence_reuses_evidence_coverage_verbatim(self):
        summary = contradiction_summary()
        result = evaluate_thesis_risk(
            summary, evidence_coverage=EvidenceCoverageLevel.PARTIAL, evaluated_at=EVALUATED_AT
        )
        assert result.confidence is EvidenceCoverageLevel.PARTIAL


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_finding(self):
        classified = classification(ObservationEpistemicStatus.CONTRADICTED, challenging_count=1)
        summary = contradiction_summary(classified)
        first = evaluate_thesis_risk(summary, evidence_coverage=EvidenceCoverageLevel.FULL, evaluated_at=EVALUATED_AT)
        second = evaluate_thesis_risk(summary, evidence_coverage=EvidenceCoverageLevel.FULL, evaluated_at=EVALUATED_AT)
        assert first == second
