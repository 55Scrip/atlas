"""Tests for `atlas.alpha.decision_memory.engine` -- deterministic
content hashing, structured change detection, and the comparison/
portfolio-breakdown helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_memory.engine import (
    DecisionSnapshotInputs,
    build_decision_memory,
    build_portfolio_decision_memory_breakdown,
    build_snapshot,
    compare_decision_memories,
    detect_decision_change,
)
from atlas.alpha.decision_memory.models import ChangeDirection, DecisionMemory, DecisionTimeline, DecisionTimelineEntry
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


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


class TestBuildSnapshot:
    def test_content_hash_is_deterministic_for_identical_inputs(self):
        a = build_snapshot("c1", _inputs(), recorded_at=NOW)
        b = build_snapshot("c1", _inputs(), recorded_at=LATER)
        assert a.content_hash == b.content_hash

    def test_content_hash_differs_when_action_differs(self):
        a = build_snapshot("c1", _inputs(action=DecisionAction.HOLD), recorded_at=NOW)
        b = build_snapshot("c1", _inputs(action=DecisionAction.BUY), recorded_at=NOW)
        assert a.content_hash != b.content_hash

    def test_content_hash_ignores_recorded_at(self):
        a = build_snapshot("c1", _inputs(), recorded_at=NOW)
        b = build_snapshot("c1", _inputs(), recorded_at=LATER)
        assert a.content_hash == b.content_hash
        assert a.recorded_at != b.recorded_at

    def test_blocker_codes_are_sorted(self):
        snapshot = build_snapshot("c1", _inputs(blocker_codes=("z_code", "a_code")), recorded_at=NOW)
        assert snapshot.blocker_codes == ("a_code", "z_code")

    def test_content_hash_differs_when_blocker_order_differs_in_input_but_not_after_sorting(self):
        a = build_snapshot("c1", _inputs(blocker_codes=("a", "b")), recorded_at=NOW)
        b = build_snapshot("c1", _inputs(blocker_codes=("b", "a")), recorded_at=NOW)
        assert a.content_hash == b.content_hash


class TestDetectDecisionChange:
    def test_baseline_when_no_previous(self):
        current = build_snapshot("c1", _inputs(), recorded_at=NOW)
        change = detect_decision_change(None, current, detected_at=NOW)
        assert change.is_baseline is True
        assert change.previous_action is None
        assert change.conviction_direction is None
        assert change.readiness_direction is None
        assert change.decision_path_direction is None

    def test_recommendation_changed_flag(self):
        previous = build_snapshot("c1", _inputs(action=DecisionAction.HOLD), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(action=DecisionAction.ADD), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.recommendation_changed is True
        assert change.previous_action is DecisionAction.HOLD
        assert change.current_action is DecisionAction.ADD

    def test_conviction_direction_stronger(self):
        previous = build_snapshot("c1", _inputs(conviction_strength=ConvictionStrength.WEAK), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(conviction_strength=ConvictionStrength.STRONG), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.conviction_direction is ChangeDirection.STRONGER

    def test_conviction_direction_weaker(self):
        previous = build_snapshot("c1", _inputs(conviction_strength=ConvictionStrength.STRONG), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(conviction_strength=ConvictionStrength.WEAK), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.conviction_direction is ChangeDirection.WEAKER

    def test_conviction_direction_unchanged(self):
        previous = build_snapshot("c1", _inputs(), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(action=DecisionAction.BUY), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.conviction_direction is ChangeDirection.UNCHANGED

    def test_readiness_direction_stronger(self):
        """Regression: `READINESS_PROXIMITY_RANK` runs the opposite
        way from `_STRENGTH_RANK` (`READY` is `0`, the *lowest*
        number) -- a naive, unnegated reuse of `_direction` reported
        moving toward `READY` as `WEAKER`. Caught by this test."""
        previous = build_snapshot("c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.readiness_direction is ChangeDirection.STRONGER

    def test_readiness_direction_weaker(self):
        previous = build_snapshot("c1", _inputs(readiness_status=DecisionReadinessStatus.READY), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(readiness_status=DecisionReadinessStatus.WAITING), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.readiness_direction is ChangeDirection.WEAKER

    def test_decision_path_direction_stronger_when_fewer_steps(self):
        previous = build_snapshot("c1", _inputs(decision_path_step_count=3), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(decision_path_step_count=1), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.decision_path_direction is ChangeDirection.STRONGER

    def test_decision_path_direction_weaker_when_more_steps(self):
        previous = build_snapshot("c1", _inputs(decision_path_step_count=1), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(decision_path_step_count=3), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.decision_path_direction is ChangeDirection.WEAKER

    def test_blockers_resolved_and_added(self):
        previous = build_snapshot("c1", _inputs(blocker_codes=("monitoring_pending", "coverage_incomplete")), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(blocker_codes=("coverage_incomplete", "no_data_source")), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.blockers_resolved == ("monitoring_pending",)
        assert change.blockers_added == ("no_data_source",)

    def test_alternative_changed_by_kind(self):
        previous = build_snapshot("c1", _inputs(primary_alternative_kind=AlternativeKind.WAIT, alternative_count=1), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(primary_alternative_kind=AlternativeKind.OPEN_NEW_POSITION, alternative_count=1), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.alternative_changed is True

    def test_alternative_changed_by_count(self):
        previous = build_snapshot("c1", _inputs(alternative_count=1), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(alternative_count=2), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.alternative_changed is True

    def test_no_alternative_change_when_identical(self):
        previous = build_snapshot("c1", _inputs(primary_alternative_kind=AlternativeKind.WAIT, alternative_count=1), recorded_at=NOW)
        current = build_snapshot("c1", _inputs(primary_alternative_kind=AlternativeKind.WAIT, alternative_count=1, action=DecisionAction.BUY), recorded_at=LATER)
        change = detect_decision_change(previous, current, detected_at=LATER)
        assert change.alternative_changed is False


def _memory(case_id: str, recorded_at: datetime, *, latest_change=None) -> DecisionMemory:
    snapshot = build_snapshot(case_id, _inputs(), recorded_at=recorded_at)
    change = detect_decision_change(None, snapshot, detected_at=recorded_at)
    entry = DecisionTimelineEntry(snapshot=snapshot, change=change)
    return build_decision_memory(case_id, snapshot, None, latest_change, DecisionTimeline(case_id, (entry,)))


class TestCompareDecisionMemories:
    def test_more_recently_changed_by_timestamp(self):
        a = _memory("a", LATER)
        b = _memory("b", NOW)
        comparison = compare_decision_memories(a, b)
        assert comparison.more_recently_changed_case_id == "a"

    def test_more_stable_by_older_timestamp(self):
        a = _memory("a", LATER)
        b = _memory("b", NOW)
        comparison = compare_decision_memories(a, b)
        assert comparison.more_stable_case_id == "b"

    def test_tie_is_none(self):
        a = _memory("a", NOW)
        b = _memory("b", NOW)
        comparison = compare_decision_memories(a, b)
        assert comparison.more_recently_changed_case_id is None
        assert comparison.more_stable_case_id is None

    def test_conviction_changed_case_id(self):
        real_change = detect_decision_change(
            build_snapshot("a", _inputs(conviction_strength=ConvictionStrength.WEAK), recorded_at=NOW),
            build_snapshot("a", _inputs(conviction_strength=ConvictionStrength.STRONG), recorded_at=LATER),
            detected_at=LATER,
        )
        a = _memory("a", LATER, latest_change=real_change)
        b = _memory("b", NOW)
        comparison = compare_decision_memories(a, b)
        assert comparison.conviction_changed_case_id == "a"

    def test_blockers_disappeared_case_id(self):
        real_change = detect_decision_change(
            build_snapshot("a", _inputs(blocker_codes=("monitoring_pending",)), recorded_at=NOW),
            build_snapshot("a", _inputs(blocker_codes=()), recorded_at=LATER),
            detected_at=LATER,
        )
        a = _memory("a", LATER, latest_change=real_change)
        b = _memory("b", NOW)
        comparison = compare_decision_memories(a, b)
        assert comparison.blockers_disappeared_case_id == "a"

    def test_never_declares_an_overall_winner(self):
        a = _memory("a", LATER)
        b = _memory("b", NOW)
        comparison = compare_decision_memories(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert field_names == {
            "a",
            "b",
            "more_recently_changed_case_id",
            "more_stable_case_id",
            "conviction_changed_case_id",
            "blockers_disappeared_case_id",
        }


class TestPortfolioDecisionMemoryBreakdown:
    def test_buckets_correctly(self):
        baseline_memory = _memory("h1", NOW)
        strengthened_change = detect_decision_change(
            build_snapshot("h2", _inputs(conviction_strength=ConvictionStrength.WEAK), recorded_at=NOW),
            build_snapshot("h2", _inputs(conviction_strength=ConvictionStrength.STRONG), recorded_at=LATER),
            detected_at=LATER,
        )
        strengthened_memory = _memory("h2", LATER, latest_change=strengthened_change)
        weakened_change = detect_decision_change(
            build_snapshot("h3", _inputs(conviction_strength=ConvictionStrength.STRONG), recorded_at=NOW),
            build_snapshot("h3", _inputs(conviction_strength=ConvictionStrength.WEAK), recorded_at=LATER),
            detected_at=LATER,
        )
        weakened_memory = _memory("h3", LATER, latest_change=weakened_change)

        items = (("AAPL", baseline_memory), ("MSFT", strengthened_memory), ("NVDA", weakened_memory))
        breakdown = build_portfolio_decision_memory_breakdown(items)
        assert breakdown.stable == ("AAPL",)
        assert breakdown.recently_changed == ("MSFT", "NVDA")
        assert breakdown.recently_strengthened == ("MSFT",)
        assert breakdown.recently_weakened == ("NVDA",)
