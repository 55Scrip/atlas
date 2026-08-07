"""Contract tests for `atlas.decision_engine.contracts` (Sprint Phase 8)."""
from __future__ import annotations

import dataclasses

import pytest

from atlas.decision_engine.contracts import (
    BusinessEvaluationResult,
    EvaluationState,
    PortfolioIntelligenceResult,
    ReasoningResult,
    RecommendationOutcomeKind,
    RecommendationWithheld,
    RecommendationWithheldReason,
    StageNotImplementedReason,
    ValuationResult,
)
from atlas.decision_engine.exceptions import DecisionEngineContractError
from tests.unit.decision_engine._fixtures import GENERATED_AT


class TestNotEvaluatedResultsRequireAReason:
    def test_business_evaluation_result_requires_reason_when_not_evaluated(self):
        with pytest.raises(DecisionEngineContractError):
            BusinessEvaluationResult(state=EvaluationState.NOT_EVALUATED, reason=None)

    def test_valuation_result_requires_reason_when_not_evaluated(self):
        with pytest.raises(DecisionEngineContractError):
            ValuationResult(state=EvaluationState.NOT_EVALUATED, reason=None)

    def test_portfolio_intelligence_result_requires_reason_when_not_evaluated(self):
        with pytest.raises(DecisionEngineContractError):
            PortfolioIntelligenceResult(state=EvaluationState.NOT_EVALUATED, reason=None)

    def test_reasoning_result_requires_blocked_by_when_not_evaluated(self):
        with pytest.raises(DecisionEngineContractError):
            ReasoningResult(state=EvaluationState.NOT_EVALUATED, blocked_by=())

    def test_valid_not_evaluated_results_construct_cleanly(self):
        business = BusinessEvaluationResult(
            state=EvaluationState.NOT_EVALUATED,
            reason=StageNotImplementedReason.EVALUATOR_NOT_IMPLEMENTED,
        )
        assert business.state is EvaluationState.NOT_EVALUATED


class TestRecommendationWithheldIsStructurallyRestricted:
    def test_kind_must_be_recommendation_withheld(self):
        with pytest.raises(DecisionEngineContractError):
            RecommendationWithheld(
                kind=RecommendationOutcomeKind.DIRECTIONAL,
                reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED,
                missing_evaluations=(),
                required_before_recommendation=(),
                generated_at=GENERATED_AT,
            )

    def test_has_no_direction_field(self):
        outcome = RecommendationWithheld(
            kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
            reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED,
            missing_evaluations=(),
            required_before_recommendation=(),
            generated_at=GENERATED_AT,
        )
        field_names = {f.name for f in dataclasses.fields(outcome)}
        assert "direction" not in field_names

    def test_has_no_conviction_field(self):
        outcome = RecommendationWithheld(
            kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
            reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED,
            missing_evaluations=(),
            required_before_recommendation=(),
            generated_at=GENERATED_AT,
        )
        field_names = {f.name for f in dataclasses.fields(outcome)}
        assert "conviction" not in field_names
        assert "conviction_level" not in field_names

    def test_is_frozen(self):
        outcome = RecommendationWithheld(
            kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
            reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED,
            missing_evaluations=(),
            required_before_recommendation=(),
            generated_at=GENERATED_AT,
        )
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            outcome.reason = RecommendationWithheldReason.EVIDENCE_INSUFFICIENT  # type: ignore[misc]
