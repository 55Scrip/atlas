"""Business Evaluation stage tests (Sprint 2, Phase 6).

Test names below map directly to the Sprint's own required scenario
list. Two scenario names from that list — "strong business" and "weak
business" — are deliberately *not* reproduced as test names here: this
evaluator makes no business-quality judgment at all (locked scope), so
naming a test `test_strong_business` would misdescribe what it actually
proves. What those two scenarios really exercise is evidence direction
classification — a Case whose recorded Evidence is entirely `SUPPORTS`,
and one whose recorded Evidence is entirely `CHALLENGES` — covered below
as `test_case_with_only_supporting_evidence` and
`test_case_with_only_challenging_evidence`, each with an explicit
assertion that no business-quality verdict is produced either way.
"""
from __future__ import annotations

import dataclasses

from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import (
    DecisionEngineInput,
    DurabilityFinding,
    DurabilityNotAssessableReason,
    EvaluationState,
    EvidenceCoverageLevel,
    EvidenceGapKind,
    ObservationEpistemicStatus,
)
from atlas.decision_engine.pipeline import run_pipeline
from atlas.decision_engine.stages.business_evaluation import evaluate_business
from tests.unit.decision_engine._fixtures import (
    CASE_ID,
    EVALUATED_AT,
    GENERATED_AT,
    build_decision,
    build_evidence,
    build_observation,
)


class TestEmptyBusinessInformation:
    def test_no_observations_and_no_evidence_yields_a_real_evaluated_result(self):
        """Sprint 2 Phase 3: a genuinely empty Case is not a failure to
        evaluate — "no evidence recorded" is itself a real, honest,
        deterministic finding."""
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = evaluate_business(engine_input)
        assert result.state is EvaluationState.EVALUATED
        assert result.evidence_quality.total_evidence_count == 0
        assert result.evidence_quality.coverage is EvidenceCoverageLevel.NOT_APPLICABLE
        assert result.evidence_quality.observation_classifications == ()
        assert any(
            gap.kind is EvidenceGapKind.NO_EVIDENCE_RECORDED
            for gap in result.evidence_quality.evidence_gaps
        )

    def test_durability_is_insufficient_input_even_when_empty(self):
        engine_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        result = evaluate_business(engine_input)
        assert result.durability == DurabilityFinding(
            state=EvaluationState.INSUFFICIENT_INPUT,
            reason=DurabilityNotAssessableReason.NO_BUSINESS_FACT_DATA_IN_INPUT,
        )


class TestCaseWithOnlySupportingEvidence:
    """The Sprint's own "strong business" scenario — a Case whose
    recorded Evidence is entirely `SUPPORTS`. Classified as evidence
    *direction*, never as a business-quality verdict."""

    def test_observation_is_classified_supported(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        result = evaluate_business(engine_input)
        [classification] = result.evidence_quality.observation_classifications
        assert classification.status is ObservationEpistemicStatus.SUPPORTED
        assert classification.supporting_evidence_count == 1
        assert classification.challenging_evidence_count == 0
        assert result.evidence_quality.coverage is EvidenceCoverageLevel.FULL

    def test_no_business_quality_verdict_is_produced(self):
        """Confirms the locked prohibition directly: no field anywhere
        on the result names a business-quality, moat, management, or
        growth conclusion, regardless of how favorable the evidence
        looks."""
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        result = evaluate_business(engine_input)
        result_field_names = {f.name for f in dataclasses.fields(result)}
        assert result_field_names == {"state", "reason", "durability", "evidence_quality"}
        durability_field_names = {f.name for f in dataclasses.fields(result.durability)}
        assert "moat" not in durability_field_names
        assert "business_quality" not in durability_field_names
        assert "management" not in durability_field_names
        assert "growth_quality" not in durability_field_names
        assert "competitive_position" not in durability_field_names
        assert "balance_sheet" not in durability_field_names


class TestCaseWithOnlyChallengingEvidence:
    """The Sprint's own "weak business" scenario — a Case whose recorded
    Evidence is entirely `CHALLENGES`."""

    def test_observation_is_classified_challenged(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.CHALLENGES)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        result = evaluate_business(engine_input)
        [classification] = result.evidence_quality.observation_classifications
        assert classification.status is ObservationEpistemicStatus.CHALLENGED
        assert classification.supporting_evidence_count == 0
        assert classification.challenging_evidence_count == 1

    def test_still_no_business_quality_verdict_is_produced(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.CHALLENGES)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        result = evaluate_business(engine_input)
        assert result.durability.state is EvaluationState.INSUFFICIENT_INPUT


class TestMixedEvidence:
    def test_different_observations_get_independently_correct_classifications(self):
        supported_obs = build_observation(subject="ASML", statement="Revenue grew.")
        challenged_obs = build_observation(subject="ASML", statement="Margins compressed.")
        assumed_obs = build_observation(subject="ASML", statement="New product announced.")
        supporting_evidence = build_evidence(observation=supported_obs, direction=Direction.SUPPORTS)
        challenging_evidence = build_evidence(
            observation=challenged_obs, direction=Direction.CHALLENGES
        )
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(supported_obs, challenged_obs, assumed_obs),
            evidence=(supporting_evidence, challenging_evidence),
        )
        result = evaluate_business(engine_input)
        by_id = {c.observation_id: c for c in result.evidence_quality.observation_classifications}
        assert by_id[supported_obs.id].status is ObservationEpistemicStatus.SUPPORTED
        assert by_id[challenged_obs.id].status is ObservationEpistemicStatus.CHALLENGED
        assert by_id[assumed_obs.id].status is ObservationEpistemicStatus.ASSUMED
        assert result.evidence_quality.coverage is EvidenceCoverageLevel.PARTIAL


class TestContradictoryEvidence:
    def test_one_observation_with_both_directions_is_contradicted(self):
        observation = build_observation()
        supporting = build_evidence(
            observation=observation, direction=Direction.SUPPORTS, statement="Guidance raised."
        )
        challenging = build_evidence(
            observation=observation,
            direction=Direction.CHALLENGES,
            statement="A competitor undercut pricing the same week.",
        )
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(supporting, challenging),
        )
        result = evaluate_business(engine_input)
        [classification] = result.evidence_quality.observation_classifications
        assert classification.status is ObservationEpistemicStatus.CONTRADICTED
        assert classification.supporting_evidence_count == 1
        assert classification.challenging_evidence_count == 1
        # A contradicted observation still counts toward coverage — it
        # has real evidence, just evidence that disagrees.
        assert result.evidence_quality.coverage is EvidenceCoverageLevel.FULL


class TestMissingOrInsufficientEvidence:
    def test_observation_with_zero_linked_evidence_is_assumed(self):
        observation = build_observation()
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
        )
        result = evaluate_business(engine_input)
        [classification] = result.evidence_quality.observation_classifications
        assert classification.status is ObservationEpistemicStatus.ASSUMED
        assert result.evidence_quality.coverage is EvidenceCoverageLevel.NONE
        assert any(
            gap.kind is EvidenceGapKind.OBSERVATION_WITHOUT_EVIDENCE
            and gap.reference == str(observation.id)
            for gap in result.evidence_quality.evidence_gaps
        )

    def test_decision_without_a_linked_observation_is_a_named_gap(self):
        decision = build_decision()
        assert decision.observation_id is None
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            decisions=(decision,),
        )
        result = evaluate_business(engine_input)
        assert any(
            gap.kind is EvidenceGapKind.DECISION_WITHOUT_LINKED_OBSERVATION
            and gap.reference == str(decision.id)
            for gap in result.evidence_quality.evidence_gaps
        )


class TestDeterminismOfTheRealEvaluator:
    def test_identical_input_produces_a_deeply_equal_result(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        first = evaluate_business(engine_input)
        second = evaluate_business(engine_input)
        assert first == second


class TestPureFunctionBehaviour:
    def test_no_side_effects_engine_input_is_unchanged(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        before = dataclasses.replace(engine_input)
        evaluate_business(engine_input)
        assert engine_input == before

    def test_calling_twice_does_not_change_the_second_result(self):
        """No hidden global/module-level mutable state carried between calls."""
        empty_input = DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT)
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        populated_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        evaluate_business(populated_input)
        result = evaluate_business(empty_input)
        assert result.evidence_quality.total_evidence_count == 0


class TestPipelineStillEndsInRecommendationWithheld:
    def test_recommendation_withheld_still_returned_with_real_business_evaluation(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert output.business_evaluation.state is EvaluationState.EVALUATED
        assert output.recommendation.kind.value == "recommendation_withheld"

    def test_reasoning_is_evaluated_with_empty_blocked_by(self):
        """Sprint 5: Reasoning is now real too (see
        `test_reasoning_stage.py`), assembling an audit trail from the
        three upstream results — `EVALUATED`, with `blocked_by` empty."""
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        assert output.reasoning.state is EvaluationState.EVALUATED
        assert output.reasoning.blocked_by == ()

    def test_no_conviction_is_produced(self):
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert not hasattr(output.recommendation, "conviction")
        assert not hasattr(output.recommendation, "conviction_level")

    def test_no_recommendation_direction_is_produced(self):
        output = run_pipeline(
            DecisionEngineInput(case_id=CASE_ID, evaluated_at=EVALUATED_AT),
            generated_at=GENERATED_AT,
        )
        assert not hasattr(output.recommendation, "direction")


class TestNoNumericScoresAnywhere:
    def test_evidence_quality_findings_has_no_score_or_percentage_field(self):
        observation = build_observation()
        evidence = build_evidence(observation=observation, direction=Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=CASE_ID,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(evidence,),
        )
        result = evaluate_business(engine_input)
        field_names = {f.name for f in dataclasses.fields(result.evidence_quality)}
        forbidden = {"score", "percentage", "probability", "confidence_score", "quality_score"}
        assert field_names.isdisjoint(forbidden)
        # The three integer fields present are plain counts, not scores —
        # confirm they are literally the counts of real recorded items.
        assert result.evidence_quality.total_evidence_count == 1
        assert result.evidence_quality.supporting_evidence_count == 1
