"""Cross-layer consistency property tests for Decision Explanation
(Deliverable 11). Exhaustive over the closed vocabularies involved --
the same discipline `tests/unit/alpha/decision_memory
/test_cross_layer_consistency.py` already established for its own
rank-direction convention."""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

import pytest

from atlas.alpha.decision_explanation.engine import build_decision_explanation, detect_decision_explanation_change
from atlas.alpha.decision_explanation.models import ChangeDirection, ExplanationReferenceKind
from atlas.alpha.decision_path.models import DecisionPath, FinalReachableState
from atlas.alpha.decision_readiness.models import DecisionReadiness, DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction, InvestmentDecision
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationConviction, RecommendationStability

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_CASE_ID = "case-1"

_STRENGTH_ORDER = [
    ConvictionStrength.UNAVAILABLE,
    ConvictionStrength.VERY_WEAK,
    ConvictionStrength.WEAK,
    ConvictionStrength.MODERATE,
    ConvictionStrength.STRONG,
    ConvictionStrength.VERY_STRONG,
]


def _explanation_with_strength(strength: ConvictionStrength):
    decision = InvestmentDecision(
        case_id=_CASE_ID, action=DecisionAction.HOLD, qualifiers=(), supporting_reasons=(), blockers=(), change_trigger=None, generated_at=_NOW
    )
    conviction = RecommendationConviction(
        case_id=_CASE_ID,
        action=DecisionAction.HOLD,
        strength=strength,
        stability=RecommendationStability.STABLE,
        supporting_reasons=(),
        limiting_reasons=(),
        strengthening_trigger=None,
        generated_at=_NOW,
    )
    readiness = DecisionReadiness(case_id=_CASE_ID, status=DecisionReadinessStatus.WAITING, blockers=(), supporting_reasons=(), generated_at=_NOW)
    path = DecisionPath(
        case_id=_CASE_ID,
        current_action=DecisionAction.HOLD,
        current_strength=strength,
        steps=(),
        immediate_blocker=None,
        next_achievable_improvement=None,
        final_reachable_state=FinalReachableState.FULLY_REACHABLE,
        generated_at=_NOW,
    )
    return build_decision_explanation(
        _CASE_ID,
        decision=decision,
        conviction=conviction,
        readiness=readiness,
        path=path,
        latest_snapshot_hash=None,
        weak_dependencies=(),
        finding_nodes=(),
        generated_at=_NOW,
    )


class TestConvictionDirectionNeverContradictsTheRealRank:
    """Exhaustive over every ordered pair of `ConvictionStrength` --
    `conviction_direction` must agree with `_STRENGTH_ORDER`'s own real
    ordering in every one of the 36 cases, never inverted."""

    @pytest.mark.parametrize("previous,current", list(product(_STRENGTH_ORDER, _STRENGTH_ORDER)))
    def test_direction_matches_the_real_rank_order(self, previous, current):
        change = detect_decision_explanation_change(
            _explanation_with_strength(previous), _explanation_with_strength(current), detected_at=_NOW
        )
        previous_rank = _STRENGTH_ORDER.index(previous)
        current_rank = _STRENGTH_ORDER.index(current)

        if previous_rank == current_rank:
            assert change is None or change.conviction_direction is None
            return

        assert change is not None
        if current_rank > previous_rank:
            assert change.conviction_direction is ChangeDirection.STRONGER
        else:
            assert change.conviction_direction is ChangeDirection.WEAKER


class TestReferenceKindsAreAlwaysOneOfTheFourClosedValues:
    def test_reference_kind_is_never_an_ad_hoc_string(self):
        explanation = _explanation_with_strength(ConvictionStrength.MODERATE)
        for finding in list(explanation.chain.supporting) + list(explanation.chain.blocking):
            assert finding.reference.kind in set(ExplanationReferenceKind)


class TestNoReferenceIsEverAnonymous:
    """Deliverable 4 -- 'nothing anonymous.' Every reference's own `id`
    must be a real, non-empty string; an empty or `None`-like id would
    be exactly the anonymous reference the brief forbids."""

    def test_every_reference_id_is_a_real_non_empty_string(self):
        explanation = _explanation_with_strength(ConvictionStrength.WEAK)
        for finding in list(explanation.chain.supporting) + list(explanation.chain.blocking):
            assert isinstance(finding.reference.id, str)
            assert finding.reference.id != ""
