"""Tests for `ComputedDirectionalRecommendation` and its supporting types
(`atlas.analysis_engine.recommendation` -- DE-007 "Implementation Step
1").

These tests construct the type directly, with real
`atlas.decision_engine.contracts` sub-objects pulled from an actual
pipeline run (`run_populated()`), to prove the shape and its validation
are correct. None of them route through `evaluate_recommendation_gate` to
get a directional outcome -- no Direction selector exists yet (see
`recommendation.py`'s own module docstring), and fabricating one here
would be exactly the "do not invent a decision rule" constraint this
sprint forbids. `test_recommendation.py` already covers, and continues to
cover unchanged, that the actual gate function only ever returns
`RecommendationWithheld`.
"""
from __future__ import annotations

import pytest

from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.recommendation import (
    ComputedDirectionalRecommendation,
    RecommendationAlternative,
    RecommendationConvictionLevel,
    RecommendationDirection,
    RecommendationGateResult,
    RecommendationReasoning,
)
from atlas.decision_engine.contracts import (
    RecommendationOutcomeKind,
    RecommendationWithheld,
    RecommendationWithheldReason,
)
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_populated


def _real_reasoning() -> RecommendationReasoning:
    """Built from a real pipeline run's own `ReasoningFinding`, never
    hand-fabricated -- proves requirement 7 (reasoning reuses the
    existing structures correctly, not a parallel shape)."""
    _, output = run_populated()
    finding = output.reasoning.finding
    assert finding is not None
    return RecommendationReasoning(
        current_situation=finding.current_situation,
        supporting_evidence=finding.supporting_evidence,
        contradicting_evidence=finding.contradicting_evidence,
        portfolio_context=finding.portfolio_context,
        what_would_change=(),
    )


def _real_portfolio_factors():
    _, output = run_populated()
    factors = output.portfolio_intelligence.portfolio_factors
    assert factors is not None
    return factors


def _valid_recommendation(**overrides) -> ComputedDirectionalRecommendation:
    _, output = run_populated()
    fields = dict(
        recommendation_instance_id="test-instance-1",
        case_id=output.case_id,
        generated_at=GENERATED_AT,
        direction=RecommendationDirection.BUY,
        direction_statement="Current evidence suggests this position may be worth initiating.",
        conviction_level=RecommendationConvictionLevel.MEDIUM,
        conviction_reason="Evidence coverage is full; one open question remains unresolved.",
        reasoning=_real_reasoning(),
        portfolio_factors=_real_portfolio_factors(),
        alternatives=(RecommendationAlternative(label="Wait", rationale="No urgency signal present."),),
    )
    fields.update(overrides)
    return ComputedDirectionalRecommendation(**fields)


class TestConstructionValidatesRequiredFields:
    """Requirement 3."""

    def test_valid_construction_succeeds(self):
        recommendation = _valid_recommendation()
        assert recommendation.direction is RecommendationDirection.BUY

    def test_empty_instance_id_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(recommendation_instance_id="")

    def test_blank_instance_id_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(recommendation_instance_id="   ")

    def test_empty_direction_statement_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(direction_statement="")

    def test_empty_conviction_reason_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(conviction_reason="")

    def test_alternative_requires_non_empty_label_and_rationale(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationAlternative(label="", rationale="Some rationale.")
        with pytest.raises(AnalysisEngineContractError):
            RecommendationAlternative(label="Wait", rationale="")


class TestDirectionEnum:
    """Requirement 4 -- exactly the six DE-001 §2 directions, never the
    Investor's own BUY/SELL/HOLD/WATCH/PASS decision type."""

    def test_exactly_six_members(self):
        assert len(RecommendationDirection) == 6

    def test_members_match_doctrine(self):
        assert {member.value for member in RecommendationDirection} == {
            "buy",
            "add",
            "hold",
            "trim",
            "exit",
            "no_action",
        }

    def test_does_not_reuse_investor_decision_vocabulary(self):
        """The Investor's own decision type includes SELL/WATCH/PASS,
        none of which exist here -- DE-006 §4's boundary, enforced
        structurally."""
        values = {member.value for member in RecommendationDirection}
        assert "sell" not in values
        assert "watch" not in values
        assert "pass" not in values

    def test_construction_rejects_non_enum_direction(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(direction="buy")  # a bare string, not the enum


class TestNoPersistenceOrLifecycleFields:
    """Requirement 5 -- DE-007 §8A's explicit "deliberately absent" list."""

    def test_no_status_field(self):
        recommendation = _valid_recommendation()
        assert not hasattr(recommendation, "status")

    def test_no_response_state_fields(self):
        recommendation = _valid_recommendation()
        for forbidden in ("state", "accepted", "dismissed", "acted_upon", "responded_at"):
            assert not hasattr(recommendation, forbidden)

    def test_no_historical_snapshot_fields(self):
        recommendation = _valid_recommendation()
        for forbidden in ("snapshotted_at", "superseded_at", "supersedes", "superseded_by"):
            assert not hasattr(recommendation, forbidden)

    def test_no_version_field(self):
        recommendation = _valid_recommendation()
        assert not hasattr(recommendation, "version")


class TestNoExecutionGuidance:
    """Requirement 6 -- DE-007 §4's one-way dependency: Execution Guidance
    references a Recommendation; a Recommendation never references
    Execution Guidance."""

    def test_no_execution_guidance_field(self):
        recommendation = _valid_recommendation()
        for forbidden in (
            "execution_guidance",
            "execution_guidance_id",
            "target_allocation_range",
            "execution_range",
            "accumulation_approach",
            "urgency",
        ):
            assert not hasattr(recommendation, forbidden)


class TestReasoningReusesExistingStructures:
    """Requirement 7."""

    def test_reasoning_fields_are_the_real_decision_engine_types(self):
        _, output = run_populated()
        finding = output.reasoning.finding
        assert finding is not None
        reasoning = RecommendationReasoning(
            current_situation=finding.current_situation,
            supporting_evidence=finding.supporting_evidence,
            contradicting_evidence=finding.contradicting_evidence,
            portfolio_context=finding.portfolio_context,
            what_would_change=(),
        )
        # Identity, not just equality -- the exact same objects the real
        # pipeline produced, never copied or re-derived.
        assert reasoning.current_situation is finding.current_situation
        assert reasoning.supporting_evidence is finding.supporting_evidence
        assert reasoning.contradicting_evidence is finding.contradicting_evidence
        assert reasoning.portfolio_context is finding.portfolio_context

    def test_portfolio_factors_is_the_real_decision_engine_type(self):
        recommendation = _valid_recommendation()
        _, output = run_populated()
        assert type(recommendation.portfolio_factors) is type(
            output.portfolio_intelligence.portfolio_factors
        )


class TestRecommendationConvictionCannotSilentlyReceiveAnalysisConvictionLevel:
    """Requirement 8 -- DE-007 §11's central resolved ambiguity: the two
    Conviction scales must never be interchangeable."""

    def test_analysis_engine_conviction_level_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(conviction_level=ConvictionLevel.VERY_HIGH)

    def test_bare_string_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            _valid_recommendation(conviction_level="high")

    def test_the_three_real_levels_are_accepted(self):
        for level in (
            RecommendationConvictionLevel.HIGH,
            RecommendationConvictionLevel.MEDIUM,
            RecommendationConvictionLevel.LOW,
        ):
            recommendation = _valid_recommendation(conviction_level=level)
            assert recommendation.conviction_level is level


class TestRecommendationGateResultRepresentsBothVariants:
    """Requirement 9, adapted to the actual architecture: the Union lives
    on `RecommendationGateResult` (`atlas.analysis_engine`), not on
    `atlas.decision_engine.contracts.DecisionEngineOutput` -- see
    `recommendation.py`'s own docstring for why (Conviction is this
    package's exclusive domain; `atlas.decision_engine` may never import
    it)."""

    def test_accepts_recommendation_withheld(self):
        withheld = RecommendationWithheld(
            kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
            reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED,
            missing_evaluations=(),
            required_before_recommendation=(),
            generated_at=GENERATED_AT,
        )
        result = RecommendationGateResult(
            recommendation=withheld, conviction_gate_met=False, conviction=_flat_conviction()
        )
        assert result.recommendation is withheld

    def test_accepts_computed_directional_recommendation(self):
        directional = _valid_recommendation()
        result = RecommendationGateResult(
            recommendation=directional, conviction_gate_met=True, conviction=_flat_conviction()
        )
        assert result.recommendation is directional

    def test_decision_engine_output_recommendation_type_is_unwidened(self):
        """Confirms the deliberate boundary: DecisionEngineOutput itself
        was NOT changed by this sprint."""
        import inspect

        from atlas.decision_engine.contracts import DecisionEngineOutput

        annotation = inspect.get_annotations(DecisionEngineOutput, eval_str=False)["recommendation"]
        assert "ComputedDirectionalRecommendation" not in annotation
        assert annotation == "RecommendationWithheld"


def _flat_conviction():
    from atlas.analysis_engine.conviction import ConvictionAssessment

    return ConvictionAssessment(level=ConvictionLevel.MODERATE, reasons=())
