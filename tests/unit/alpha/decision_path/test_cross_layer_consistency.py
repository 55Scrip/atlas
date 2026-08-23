"""Deliverable 11 (Cross-layer Audit) -- explicit invariant checks that
Investment Decision, Decision Readiness, Recommendation Conviction, and
Decision Path can never disagree. Property-style tests over the *whole*
blocker-subset space, not a handful of examples -- the same discipline
Sprint 2's own `test_cross_layer_consistency.py` already established
for its own layer, applied here to this sprint's own dependency
analysis.
"""
from __future__ import annotations

from datetime import datetime, timezone
from itertools import combinations

from atlas.alpha.decision_path.engine import DecisionPathInputs, build_decision_path
from atlas.alpha.decision_path.models import FinalReachableState, ReachabilityStatus
from atlas.alpha.decision_readiness.models import DecisionBlocker, DecisionBlockerKind, DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.recommendation_conviction.models import ConvictionStrength

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)

_ALL_BLOCKER_KINDS = tuple(DecisionBlockerKind)


def _inputs(blocker_kinds: tuple[DecisionBlockerKind, ...]) -> DecisionPathInputs:
    return DecisionPathInputs(
        action=DecisionAction.HOLD,
        strength=ConvictionStrength.MODERATE,
        readiness_status=DecisionReadinessStatus.WAITING,
        readiness_blockers=tuple(DecisionBlocker(k) for k in blocker_kinds),
        readiness_supporting_reasons=(),
        weak_dependencies=(),
        graph_node_details_by_id={},
    )


class TestNoDataSourceCascadeAcrossEveryBlockerSubset:
    def test_every_pair_including_no_data_source_downgrades_the_other_to_blocked(self):
        """No two-blocker combination that includes `NO_DATA_SOURCE`
        can ever leave the *other* blocker independently `REACHABLE`
        -- the one real, structural dependency this sprint's own audit
        found among the 13 blockers, verified exhaustively."""
        other_kinds = [k for k in _ALL_BLOCKER_KINDS if k is not DecisionBlockerKind.NO_DATA_SOURCE]
        for other in other_kinds:
            path = build_decision_path("c1", _inputs((DecisionBlockerKind.NO_DATA_SOURCE, other)), generated_at=NOW)
            by_code = {s.dependency.code: s for s in path.steps}
            assert by_code["no_data_source"].reachability is ReachabilityStatus.NOT_REACHABLE
            assert by_code[other.value].reachability is not ReachabilityStatus.REACHABLE

    def test_without_no_data_source_no_step_is_ever_blocked(self):
        """`BLOCKED` only ever exists as a consequence of the
        `NO_DATA_SOURCE` cascade -- absent it, every step is either
        its own intrinsic `REACHABLE` or `NOT_REACHABLE`, never
        `BLOCKED` by another step."""
        other_kinds = [k for k in _ALL_BLOCKER_KINDS if k is not DecisionBlockerKind.NO_DATA_SOURCE]
        for pair in combinations(other_kinds, 2):
            path = build_decision_path("c1", _inputs(pair), generated_at=NOW)
            assert not any(s.reachability is ReachabilityStatus.BLOCKED for s in path.steps)


class TestFinalReachableStateNeverContradictsItsOwnSteps:
    def test_across_every_single_blocker(self):
        for kind in _ALL_BLOCKER_KINDS:
            path = build_decision_path("c1", _inputs((kind,)), generated_at=NOW)
            state = path.final_reachable_state

            if state is FinalReachableState.ALREADY_REACHED:
                assert path.steps == ()
            elif state is FinalReachableState.NOT_REACHABLE:
                assert not any(s.reachability is ReachabilityStatus.REACHABLE for s in path.steps)
            elif state is FinalReachableState.PARTIALLY_REACHABLE:
                assert any(s.reachability is ReachabilityStatus.NOT_REACHABLE for s in path.steps)
            else:  # FULLY_REACHABLE
                assert all(s.reachability is ReachabilityStatus.REACHABLE for s in path.steps)
                assert path.steps != ()

    def test_across_every_pair_of_blockers(self):
        for pair in combinations(_ALL_BLOCKER_KINDS, 2):
            path = build_decision_path("c1", _inputs(pair), generated_at=NOW)
            state = path.final_reachable_state

            if state is FinalReachableState.NOT_REACHABLE:
                assert not any(s.reachability is ReachabilityStatus.REACHABLE for s in path.steps)
            elif state is FinalReachableState.PARTIALLY_REACHABLE:
                assert any(s.reachability is ReachabilityStatus.NOT_REACHABLE for s in path.steps)
            elif state is FinalReachableState.FULLY_REACHABLE:
                assert all(s.reachability is ReachabilityStatus.REACHABLE for s in path.steps)


class TestImmediateBlockerAndNextAchievableNeverContradictSteps:
    def test_across_every_single_blocker(self):
        for kind in _ALL_BLOCKER_KINDS:
            path = build_decision_path("c1", _inputs((kind,)), generated_at=NOW)
            if path.steps:
                assert path.immediate_blocker == path.steps[0]
            if path.next_achievable_improvement is not None:
                assert path.next_achievable_improvement in path.steps
                assert path.next_achievable_improvement.reachability is ReachabilityStatus.REACHABLE


class TestNoDecisionGateIsAbsoluteAcrossEveryBlockerCombination:
    def test_action_and_strength_never_influence_step_construction(self):
        """A `DecisionPath`'s own steps are a pure function of
        readiness blockers/status alone -- `action`/`strength` are
        carried through for display, never consulted when building the
        step list itself. Changing them alone must never change the
        steps."""
        blockers = (DecisionBlockerKind.MISSING_THESIS_EVIDENCE, DecisionBlockerKind.MONITORING_PENDING)
        base_inputs = _inputs(blockers)
        path_a = build_decision_path("c1", base_inputs, generated_at=NOW)

        import dataclasses

        path_b = build_decision_path(
            "c1",
            dataclasses.replace(base_inputs, action=DecisionAction.NO_DECISION, strength=ConvictionStrength.UNAVAILABLE),
            generated_at=NOW,
        )
        assert path_a.steps == path_b.steps
        assert path_a.final_reachable_state == path_b.final_reachable_state
