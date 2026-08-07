"""Structural and contract-completeness tests for
`atlas.decision_engine.pipeline.run_pipeline` (Sprint Phase 8)."""
from __future__ import annotations

from atlas.decision_engine.contracts import (
    EvaluationState,
    MissingEvaluationCategory,
    ReasoningBlockedBy,
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
        """Sprint 2: Business Evaluation is now real and always
        `EVALUATED` (a genuine, deterministic conclusion — even "no
        evidence recorded" — is always producible); the other three
        stages remain Sprint 1 placeholders."""
        output = run_pipeline(build_populated_input(), generated_at=GENERATED_AT)
        assert output.business_evaluation.state is EvaluationState.EVALUATED
        assert output.valuation.state is EvaluationState.NOT_EVALUATED
        assert output.portfolio_intelligence.state is EvaluationState.NOT_EVALUATED
        assert output.reasoning.state is EvaluationState.NOT_EVALUATED

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
    def test_missing_evaluations_lists_the_three_remaining_placeholder_stages(self):
        """Sprint 2: Business Evaluation is EVALUATED, so it no longer
        appears in `missing_evaluations` — only the three stages still
        unimplemented this sprint do."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert set(output.recommendation.missing_evaluations) == {
            MissingEvaluationCategory.VALUATION,
            MissingEvaluationCategory.PORTFOLIO_INTELLIGENCE,
            MissingEvaluationCategory.REASONING,
        }

    def test_required_before_recommendation_names_all_four_prerequisites(self):
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert len(output.recommendation.required_before_recommendation) == 4


class TestPipelineStageExecutionOrder:
    def test_reasoning_reflects_prior_incomplete_stages(self):
        """Sprint 2: Business Evaluation is EVALUATED, so it no longer
        blocks Reasoning — only Valuation and Portfolio Intelligence
        still do."""
        output = run_pipeline(build_minimal_input(), generated_at=GENERATED_AT)
        assert set(output.reasoning.blocked_by) == {
            ReasoningBlockedBy.VALUATION_NOT_EVALUATED,
            ReasoningBlockedBy.PORTFOLIO_INTELLIGENCE_NOT_EVALUATED,
        }

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
