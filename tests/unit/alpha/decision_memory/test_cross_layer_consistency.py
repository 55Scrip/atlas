"""Deliverable 11 (Cross-layer Audit) -- explicit invariant checks that
Decision Memory's own directions never contradict the real rank orders
Sprint 2's `recommendation_conviction` and Sprint 11's
`decision_readiness` already established. Property-style tests over
the whole strength/status space, the same discipline every prior
sprint's own `test_cross_layer_consistency.py` already established.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import product

from atlas.alpha.decision_memory.engine import DecisionSnapshotInputs, build_snapshot, detect_decision_change
from atlas.alpha.decision_memory.models import ChangeDirection
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.engine import READINESS_PROXIMITY_RANK
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)

_STRENGTH_RANK = {
    ConvictionStrength.UNAVAILABLE: -1,
    ConvictionStrength.VERY_WEAK: 0,
    ConvictionStrength.WEAK: 1,
    ConvictionStrength.MODERATE: 2,
    ConvictionStrength.STRONG: 3,
    ConvictionStrength.VERY_STRONG: 4,
}


def _inputs(**overrides) -> DecisionSnapshotInputs:
    base = dict(
        action=DecisionAction.HOLD,
        readiness_status=DecisionReadinessStatus.READY,
        blocker_codes=(),
        conviction_strength=ConvictionStrength.MODERATE,
        conviction_stability=RecommendationStability.STABLE,
        decision_path_step_count=0,
        decision_path_final_state=FinalReachableState.ALREADY_REACHED,
        primary_alternative_kind=None,
        alternative_count=0,
    )
    base.update(overrides)
    return DecisionSnapshotInputs(**base)


class TestConvictionDirectionNeverContradictsTheRealRank:
    def test_across_every_pair_of_strengths(self):
        for previous_strength, current_strength in product(ConvictionStrength, ConvictionStrength):
            previous = build_snapshot("c1", _inputs(conviction_strength=previous_strength), recorded_at=NOW)
            current = build_snapshot("c1", _inputs(conviction_strength=current_strength), recorded_at=LATER)
            change = detect_decision_change(previous, current, detected_at=LATER)

            previous_rank = _STRENGTH_RANK[previous_strength]
            current_rank = _STRENGTH_RANK[current_strength]
            if current_rank > previous_rank:
                assert change.conviction_direction is ChangeDirection.STRONGER
            elif current_rank < previous_rank:
                assert change.conviction_direction is ChangeDirection.WEAKER
            else:
                assert change.conviction_direction is ChangeDirection.UNCHANGED


class TestReadinessDirectionNeverContradictsTheRealProximityRank:
    def test_across_every_pair_of_statuses(self):
        for previous_status, current_status in product(DecisionReadinessStatus, DecisionReadinessStatus):
            previous = build_snapshot("c1", _inputs(readiness_status=previous_status), recorded_at=NOW)
            current = build_snapshot("c1", _inputs(readiness_status=current_status), recorded_at=LATER)
            change = detect_decision_change(previous, current, detected_at=LATER)

            # Lower READINESS_PROXIMITY_RANK means closer to READY --
            # moving to a lower rank is always STRONGER, never WEAKER.
            previous_proximity = READINESS_PROXIMITY_RANK[previous_status]
            current_proximity = READINESS_PROXIMITY_RANK[current_status]
            if current_proximity < previous_proximity:
                assert change.readiness_direction is ChangeDirection.STRONGER
            elif current_proximity > previous_proximity:
                assert change.readiness_direction is ChangeDirection.WEAKER
            else:
                assert change.readiness_direction is ChangeDirection.UNCHANGED


class TestBaselineNeverCarriesADirection:
    def test_across_every_action_and_status(self):
        for action, status in product(DecisionAction, DecisionReadinessStatus):
            current = build_snapshot("c1", _inputs(action=action, readiness_status=status), recorded_at=NOW)
            change = detect_decision_change(None, current, detected_at=NOW)
            assert change.is_baseline is True
            assert change.conviction_direction is None
            assert change.readiness_direction is None
            assert change.decision_path_direction is None
            assert change.previous_action is None
            assert change.recommendation_changed is False
            assert change.alternative_changed is False
            assert change.blockers_resolved == ()
            assert change.blockers_added == ()


class TestContentHashNeverDependsOnRecordedAt:
    def test_across_every_action_and_status_pair(self):
        for action, status in product(DecisionAction, DecisionReadinessStatus):
            a = build_snapshot("c1", _inputs(action=action, readiness_status=status), recorded_at=NOW)
            b = build_snapshot("c1", _inputs(action=action, readiness_status=status), recorded_at=LATER)
            assert a.content_hash == b.content_hash
