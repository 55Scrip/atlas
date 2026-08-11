"""Tests for `atlas.alpha.decision_support` (Workspace Migration Phase
1) -- the presentation-layer mapping from the already-computed
`atlas.analysis_engine.recommendation.RecommendationGateResult` onto
Atlas's own evidence-support language. Never exercises
`evaluate_recommendation_gate`/`select_direction` themselves (those are
`test_recommendation.py`/`test_direction_selector.py`'s own,
unmodified, still-passing responsibility) -- these tests only prove the
translation from an already-decided outcome to product-facing text.
"""
from __future__ import annotations

import pytest

from atlas.alpha.decision_support import DecisionSupportLevel, describe_recommendation
from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.recommendation import (
    ComputedDirectionalRecommendation,
    RecommendationAlternative,
    RecommendationConvictionLevel,
    RecommendationDirection,
    RecommendationGateResult,
    RecommendationReasoning,
)
from atlas.decision_engine.contracts import (
    MissingEvaluationCategory,
    RecommendationOutcomeKind,
    RecommendationWithheld,
    RecommendationWithheldReason,
    RequiredBeforeRecommendation,
)
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_populated


def _real_reasoning() -> RecommendationReasoning:
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


def _directional(direction: RecommendationDirection, **overrides) -> ComputedDirectionalRecommendation:
    _, output = run_populated()
    fields = dict(
        recommendation_instance_id="decision-support-test",
        case_id=output.case_id,
        generated_at=GENERATED_AT,
        direction=direction,
        direction_statement="irrelevant to this module -- never read by describe_recommendation",
        conviction_level=RecommendationConvictionLevel.MEDIUM,
        conviction_reason="test fixture",
        reasoning=_real_reasoning(),
        portfolio_factors=_real_portfolio_factors(),
    )
    fields.update(overrides)
    return ComputedDirectionalRecommendation(**fields)


def _withheld(**overrides) -> RecommendationWithheld:
    fields = dict(
        kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
        reason=RecommendationWithheldReason.EVIDENCE_INSUFFICIENT,
        missing_evaluations=(MissingEvaluationCategory.BUSINESS_EVALUATION,),
        required_before_recommendation=(RequiredBeforeRecommendation.COMPLETED_BUSINESS_EVALUATION,),
        generated_at=GENERATED_AT,
    )
    fields.update(overrides)
    return RecommendationWithheld(**fields)


def _gate_result(recommendation, *, conviction_gate_met: bool = True) -> RecommendationGateResult:
    return RecommendationGateResult(
        recommendation=recommendation,
        conviction_gate_met=conviction_gate_met,
        conviction=ConvictionAssessment(level=ConvictionLevel.HIGH, reasons=()),
    )


class TestEveryDirectionMapsToItsOwnLevel:
    """The six `RecommendationDirection` members each map to their own
    `DecisionSupportLevel` -- no two directions ever collapse onto the
    same level, and no raw direction name ever appears in the output."""

    @pytest.mark.parametrize(
        "direction,expected_level",
        [
            (RecommendationDirection.BUY, DecisionSupportLevel.ENTRY_SUPPORTED),
            (RecommendationDirection.ADD, DecisionSupportLevel.INCREASE_SUPPORTED),
            (RecommendationDirection.HOLD, DecisionSupportLevel.THESIS_INTACT),
            (RecommendationDirection.TRIM, DecisionSupportLevel.REDUCTION_SUPPORTED),
            (RecommendationDirection.EXIT, DecisionSupportLevel.EXIT_SUPPORTED),
            (RecommendationDirection.NO_ACTION, DecisionSupportLevel.NO_ACTION_SUPPORTED),
        ],
    )
    def test_direction_maps_to_expected_level(self, direction, expected_level):
        view = describe_recommendation(_gate_result(_directional(direction)))
        assert view.level is expected_level

    def test_all_six_levels_are_distinct(self):
        levels = {
            describe_recommendation(_gate_result(_directional(d))).level
            for d in RecommendationDirection
        }
        assert len(levels) == 6


class TestWithheldMapsToInsufficientEvidence:
    def test_withheld_always_maps_to_insufficient_evidence(self):
        view = describe_recommendation(_gate_result(_withheld()))
        assert view.level is DecisionSupportLevel.INSUFFICIENT_EVIDENCE

    def test_reason_never_changes_the_mapped_level(self):
        """`describe_recommendation` deliberately never branches on
        `.reason` -- confirms both `RecommendationWithheldReason` members
        map identically, per this module's own docstring."""
        engine_not_implemented = describe_recommendation(
            _gate_result(_withheld(reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED))
        )
        evidence_insufficient = describe_recommendation(
            _gate_result(_withheld(reason=RecommendationWithheldReason.EVIDENCE_INSUFFICIENT))
        )
        assert engine_not_implemented.level is DecisionSupportLevel.INSUFFICIENT_EVIDENCE
        assert evidence_insufficient.level is DecisionSupportLevel.INSUFFICIENT_EVIDENCE


class TestNoActionIsDistinctFromInsufficientEvidence:
    """The one real product decision made in this module: `NO_ACTION`
    (a real, evaluated conclusion for a security not currently held) and
    `INSUFFICIENT_EVIDENCE` (no conclusion was reachable at all) must
    never share a level, a badge label, or a statement."""

    def test_levels_differ(self):
        no_action = describe_recommendation(_gate_result(_directional(RecommendationDirection.NO_ACTION)))
        withheld = describe_recommendation(_gate_result(_withheld()))
        assert no_action.level is not withheld.level

    def test_badge_labels_differ(self):
        no_action = describe_recommendation(_gate_result(_directional(RecommendationDirection.NO_ACTION)))
        withheld = describe_recommendation(_gate_result(_withheld()))
        assert no_action.badge_label != withheld.badge_label

    def test_statements_differ(self):
        no_action = describe_recommendation(_gate_result(_directional(RecommendationDirection.NO_ACTION)))
        withheld = describe_recommendation(_gate_result(_withheld()))
        assert no_action.statement != withheld.statement


class TestNeverExposesRawDirectionVocabulary:
    """Decision Log #1: a bare `RecommendationDirection` member name/value
    (`BUY`/`ADD`/`HOLD`/`TRIM`/`EXIT`/`NO_ACTION`, standing alone as an
    imperative command) must never be the badge label or the whole
    statement. Evidence-support *sentences* legitimately contain the
    plain English verbs "exiting"/"reducing"/"increasing"/"initiating" --
    those are not commands, so this test checks exact equality against
    the raw enum forms, never a substring ban on ordinary English."""

    @pytest.mark.parametrize("direction", list(RecommendationDirection))
    def test_badge_label_is_never_the_raw_direction_name_or_value(self, direction):
        view = describe_recommendation(_gate_result(_directional(direction)))
        assert view.badge_label != direction.name
        assert view.badge_label != direction.value
        assert view.badge_label.lower() != direction.value.replace("_", " ")

    @pytest.mark.parametrize("direction", list(RecommendationDirection))
    def test_statement_is_never_the_bare_direction_word_alone(self, direction):
        view = describe_recommendation(_gate_result(_directional(direction)))
        assert view.statement != direction.name
        assert view.statement != direction.value
        assert len(view.statement.split()) > 2  # always a real sentence, never a one-word command


class TestReviewSixStateWording:
    """Migration Review §11.1's exact six-state sentence table, verified
    verbatim."""

    def test_entry_supported_statement(self):
        view = describe_recommendation(_gate_result(_directional(RecommendationDirection.BUY)))
        assert view.statement == "Current evidence supports initiating a position."

    def test_increase_supported_statement(self):
        view = describe_recommendation(_gate_result(_directional(RecommendationDirection.ADD)))
        assert view.statement == "Current evidence supports increasing exposure."

    def test_thesis_intact_statement(self):
        view = describe_recommendation(_gate_result(_directional(RecommendationDirection.HOLD)))
        assert view.statement == "Current thesis remains intact."

    def test_reduction_supported_statement(self):
        view = describe_recommendation(_gate_result(_directional(RecommendationDirection.TRIM)))
        assert view.statement == "Current evidence supports reducing exposure."

    def test_exit_supported_statement(self):
        view = describe_recommendation(_gate_result(_directional(RecommendationDirection.EXIT)))
        assert view.statement == "Current evidence supports exiting the position."

    def test_insufficient_evidence_statement(self):
        view = describe_recommendation(_gate_result(_withheld()))
        assert view.statement == "Current evidence is insufficient to support any portfolio action."


class TestDeterminism:
    def test_identical_input_produces_identical_output(self):
        gate_result = _gate_result(_directional(RecommendationDirection.TRIM))
        first = describe_recommendation(gate_result)
        second = describe_recommendation(gate_result)
        assert first == second

    def test_never_mutates_the_gate_result(self):
        recommendation = _directional(RecommendationDirection.HOLD)
        gate_result = _gate_result(recommendation)
        describe_recommendation(gate_result)
        assert gate_result.recommendation is recommendation
        assert gate_result.recommendation.direction is RecommendationDirection.HOLD


class TestAlternativesFieldIsUnused:
    """`ComputedDirectionalRecommendation.alternatives` (Opportunity
    Cost content) is never read by this presentation module -- it is
    scoped purely to `direction`/`RecommendationWithheld`, never a
    second source of truth for the level."""

    def test_alternatives_do_not_affect_the_result(self):
        with_alt = describe_recommendation(
            _gate_result(
                _directional(
                    RecommendationDirection.HOLD,
                    alternatives=(RecommendationAlternative(label="Wait", rationale="No urgency."),),
                )
            )
        )
        without_alt = describe_recommendation(_gate_result(_directional(RecommendationDirection.HOLD)))
        assert with_alt == without_alt
