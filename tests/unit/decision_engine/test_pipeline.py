"""Structural and contract-completeness tests for
`atlas.decision_engine.pipeline.run_pipeline` (Sprint Phase 8)."""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    EvaluationState,
    MissingEvaluationCategory,
    RecommendationOutcomeKind,
    RecommendationWithheldReason,
)
from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.decision_engine._fixtures import (
    GENERATED_AT,
    build_minimal_input,
    build_populated_input,
)


class TestPipelineProducesACompleteOutput:
    def test_valid_input_produces_a_complete_output(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.business_evaluation is not None
        assert output.valuation is not None
        assert output.portfolio_intelligence is not None
        assert output.reasoning is not None
        assert output.recommendation is not None

    def test_every_stage_appears_in_the_result_for_populated_input_too(self):
        """Sprints 2–5 made all four stages real and always `EVALUATED`
        (a genuine, deterministic conclusion is always producible for
        each — including Reasoning's own audit-trail assembly, even when
        most of what it assembles is "not yet assessable")."""
        output = run_pipeline(build_populated_input(), generated_at=GENERATED_AT)
        assert output.business_evaluation.state is EvaluationState.EVALUATED
        assert output.valuation.state is EvaluationState.EVALUATED
        assert output.portfolio_intelligence.state is EvaluationState.EVALUATED
        assert output.reasoning.state is EvaluationState.EVALUATED

    def test_output_carries_the_input_case_id_and_evaluated_at(self):
        engine_input = build_minimal_input()
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert output.case_id == engine_input.case_id
        assert output.evaluated_at == engine_input.evaluated_at
        assert output.generated_at == GENERATED_AT


class TestNoDirectionalRecommendationIsProduced:
    def test_no_directional_recommendation_is_produced(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_final_outcome_is_recommendation_withheld(self):
        output = run_pipeline(build_populated_input(), generated_at=GENERATED_AT)
        assert output.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        assert output.recommendation.reason is RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED

    def test_no_conviction_level_is_produced(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert not hasattr(output.recommendation, "conviction")
        assert not hasattr(output.recommendation, "conviction_level")


class TestMissingEvaluationsAreAccurate:
    def test_missing_evaluations_is_empty(self):
        """Sprint 5: all four stages are `EVALUATED`, so
        `missing_evaluations` is empty. Per the Sprint 5 lock, this is
        NOT license to generate a direction — see
        `TestRecommendationRemainsWithheldRegardlessOfMissingEvaluations`."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.recommendation.missing_evaluations == ()

    def test_required_before_recommendation_names_all_four_prerequisites(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert len(output.recommendation.required_before_recommendation) == 4


class TestPipelineStageExecutionOrder:
    def test_reasoning_blocked_by_is_empty(self):
        """Sprint 5: `ReasoningResult.state` is `EVALUATED`, so
        `blocked_by` — meaningful only for the `NOT_EVALUATED` branch —
        is empty."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.reasoning.blocked_by == ()

    def test_recommendation_derives_withheld_outcome_from_stage_states(self):
        """`missing_evaluations` is computed from real stage results, not
        hardcoded — proven by asserting it matches exactly the four
        stages whose `state` is not `EVALUATED`, read directly off the
        output rather than assumed."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        stage_results = {
            MissingEvaluationCategory.BUSINESS_EVALUATION: output.business_evaluation,
            MissingEvaluationCategory.VALUATION: output.valuation,
            MissingEvaluationCategory.PORTFOLIO_INTELLIGENCE: output.portfolio_intelligence,
            MissingEvaluationCategory.REASONING: output.reasoning,
        }
        expected_missing = {
            category
            for category, result in stage_results.items()
            if result.state is not EvaluationState.EVALUATED
        }
        assert set(output.recommendation.missing_evaluations) == expected_missing


class TestRecommendationRemainsWithheldRegardlessOfMissingEvaluations:
    """Sprint 5's own explicit invariant: an empty `missing_evaluations`
    is not license to generate a direction. Recommendation stays locked
    by implementation scope and doctrine, not by the missing-evaluations
    count — `determine_recommendation` has no conditional branch toward
    a directional outcome at all, regardless of what is or isn't
    missing."""

    def test_recommendation_withheld_despite_empty_missing_evaluations(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert output.recommendation.missing_evaluations == ()
        assert output.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        assert output.recommendation.reason is RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED

    def test_no_direction_field_exists_on_recommendation(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert not hasattr(output.recommendation, "direction")

    def test_no_conviction_field_exists_on_recommendation(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert not hasattr(output.recommendation, "conviction")
        assert not hasattr(output.recommendation, "conviction_level")
