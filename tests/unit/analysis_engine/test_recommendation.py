"""Tests for `atlas.analysis_engine.recommendation
.evaluate_recommendation_gate` (ATLAS-020 Phase 10) -- confirms it
delegates the recommendation itself entirely to
`atlas.decision_engine.stages.recommendation.determine_recommendation`
(never reimplementing it) and adds exactly one new fact, the Conviction
gate."""
from __future__ import annotations

from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.recommendation import (
    RECOMMENDATION_GATE_MINIMUM_CONVICTION,
    evaluate_recommendation_gate,
)
from atlas.decision_engine.contracts import RecommendationOutcomeKind, RecommendationWithheldReason
from atlas.decision_engine.stages.recommendation import determine_recommendation
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated


def _assessment(level: ConvictionLevel) -> ConvictionAssessment:
    return ConvictionAssessment(level=level, reasons=())


class TestRecommendationIsDelegatedNotReimplemented:
    def test_result_matches_determine_recommendation_called_directly(self):
        engine_input, output = run_minimal()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.HIGH),
            generated_at=GENERATED_AT,
        )
        expected = determine_recommendation(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            generated_at=GENERATED_AT,
        )
        assert result.recommendation == expected

    def test_still_always_recommendation_withheld(self):
        engine_input, output = run_populated()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.VERY_HIGH),
            generated_at=GENERATED_AT,
        )
        assert result.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        assert result.recommendation.reason is RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED


class TestConvictionGate:
    def test_insufficient_evidence_does_not_meet_the_gate(self):
        engine_input, output = run_minimal()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.INSUFFICIENT_EVIDENCE),
            generated_at=GENERATED_AT,
        )
        assert result.conviction_gate_met is False

    def test_low_does_not_meet_the_gate(self):
        engine_input, output = run_minimal()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.LOW),
            generated_at=GENERATED_AT,
        )
        assert result.conviction_gate_met is False

    def test_moderate_meets_the_gate(self):
        assert RECOMMENDATION_GATE_MINIMUM_CONVICTION is ConvictionLevel.MODERATE
        engine_input, output = run_minimal()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.MODERATE),
            generated_at=GENERATED_AT,
        )
        assert result.conviction_gate_met is True

    def test_very_high_meets_the_gate(self):
        engine_input, output = run_minimal()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.VERY_HIGH),
            generated_at=GENERATED_AT,
        )
        assert result.conviction_gate_met is True


class TestNoDirectionalRecommendationTypeExists:
    def test_result_has_no_direction_field(self):
        engine_input, output = run_minimal()
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.VERY_HIGH),
            generated_at=GENERATED_AT,
        )
        assert not hasattr(result, "direction")
        assert not hasattr(result.recommendation, "direction")

    def test_conviction_gate_met_does_not_flip_the_recommendation_kind(self):
        """The Conviction gate is an additional fact, not a switch that
        produces a directional outcome -- clearing it must never change
        `recommendation.kind`."""
        engine_input, output = run_minimal()
        met = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.VERY_HIGH),
            generated_at=GENERATED_AT,
        )
        not_met = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=_assessment(ConvictionLevel.LOW),
            generated_at=GENERATED_AT,
        )
        assert met.recommendation.kind is not_met.recommendation.kind
        assert met.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
