"""Tests for `atlas.analysis_engine.lifecycle.determine_life_stage`
(ATLAS-020 Phase 11) -- covers all four `LifeStage` branches and the
determinism/no-mutation guarantees every other stage in this package
already provides."""
from __future__ import annotations

from atlas.core.domain.case.value_objects import CaseId
from atlas.decision_engine.contracts import DecisionEngineInput
from atlas.analysis_engine.lifecycle import LifeStage, determine_life_stage
from tests.unit.analysis_engine._fixtures import (
    EVALUATED_AT,
    build_decision,
    build_evidence,
    build_observation,
    build_outcome,
)


class TestLifeStageBranches:
    def test_no_records_at_all_is_no_activity(self):
        result = determine_life_stage(DecisionEngineInput(case_id=CaseId(), evaluated_at=EVALUATED_AT))
        assert result.stage is LifeStage.NO_ACTIVITY
        assert result.decision_count == 0
        assert result.observation_count == 0
        assert result.outcome_count == 0

    def test_evidence_alone_without_observation_is_still_no_activity(self):
        """Evidence always exists to support/challenge an Observation; an
        Evidence-only input (constructible even though it would never
        arise from real Core writes) must not be misread as activity."""
        case_id = CaseId()
        observation = build_observation(case_id=case_id)
        evidence = build_evidence(observation=observation)
        engine_input = DecisionEngineInput(
            case_id=case_id, evaluated_at=EVALUATED_AT, evidence=(evidence,)
        )
        assert determine_life_stage(engine_input).stage is LifeStage.NO_ACTIVITY

    def test_observation_only_is_observed(self):
        case_id = CaseId()
        observation = build_observation(case_id=case_id)
        engine_input = DecisionEngineInput(
            case_id=case_id, evaluated_at=EVALUATED_AT, observations=(observation,)
        )
        result = determine_life_stage(engine_input)
        assert result.stage is LifeStage.OBSERVED
        assert result.observation_count == 1

    def test_decision_without_outcome_is_decided(self):
        case_id = CaseId()
        decision = build_decision(case_id=case_id)
        engine_input = DecisionEngineInput(
            case_id=case_id, evaluated_at=EVALUATED_AT, decisions=(decision,)
        )
        result = determine_life_stage(engine_input)
        assert result.stage is LifeStage.DECIDED
        assert result.decision_count == 1

    def test_decision_with_outcome_is_reviewed(self):
        case_id = CaseId()
        decision = build_decision(case_id=case_id)
        outcome = build_outcome(decision=decision)
        engine_input = DecisionEngineInput(
            case_id=case_id,
            evaluated_at=EVALUATED_AT,
            decisions=(decision,),
            outcomes=(outcome,),
        )
        result = determine_life_stage(engine_input)
        assert result.stage is LifeStage.REVIEWED
        assert result.outcome_count == 1

    def test_outcome_present_outranks_decision_and_observation(self):
        """First-match-wins ordering: Outcome -> Decision -> Observation.
        A Case with all three recorded is REVIEWED, not DECIDED or
        OBSERVED."""
        case_id = CaseId()
        decision = build_decision(case_id=case_id)
        outcome = build_outcome(decision=decision)
        observation = build_observation(case_id=case_id)
        engine_input = DecisionEngineInput(
            case_id=case_id,
            evaluated_at=EVALUATED_AT,
            decisions=(decision,),
            outcomes=(outcome,),
            observations=(observation,),
        )
        assert determine_life_stage(engine_input).stage is LifeStage.REVIEWED


class TestNoStatusIsWrittenAnywhere:
    def test_assessment_carries_no_case_reference_beyond_counts(self):
        """`LifeStageAssessment` must never carry anything that looks
        like a persisted status -- only counts and the derived stage."""
        case_id = CaseId()
        engine_input = DecisionEngineInput(case_id=case_id, evaluated_at=EVALUATED_AT)
        result = determine_life_stage(engine_input)
        assert not hasattr(result, "case_id")
        assert not hasattr(result, "persisted")


class TestDeterminism:
    def test_identical_input_produces_a_deeply_equal_assessment(self):
        case_id = CaseId()
        observation = build_observation(case_id=case_id)
        engine_input = DecisionEngineInput(
            case_id=case_id, evaluated_at=EVALUATED_AT, observations=(observation,)
        )
        first = determine_life_stage(engine_input)
        second = determine_life_stage(engine_input)
        assert first == second
