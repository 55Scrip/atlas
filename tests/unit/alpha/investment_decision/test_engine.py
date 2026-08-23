"""Tests for `atlas.alpha.investment_decision.engine` -- the action
mapping, every qualifier trigger in isolation, and the summary/compare/
change-detection helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.decision_support import DecisionSupportLevel
from atlas.alpha.investment_decision.engine import (
    ACTION_BY_DECISION_SUPPORT_LEVEL,
    SynthesisInputs,
    compare_decisions,
    detect_decision_change,
    summarize_decision,
    synthesize_decision,
)
from atlas.alpha.investment_decision.models import (
    DecisionAction,
    DecisionQualifierKind,
    DecisionReason,
    DecisionReasonSource,
    InvestmentDecision,
)
from atlas.alpha.stance.models import StanceLevel, StanceReasonCode

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _inputs(**overrides) -> SynthesisInputs:
    """A fully "healthy, strong" baseline -- every test overrides only
    the field(s) it actually cares about."""
    base = dict(
        decision_support_level=DecisionSupportLevel.ENTRY_SUPPORTED,
        readiness_status=DecisionReadinessStatus.READY,
        readiness_blockers=(),
        readiness_supporting_reasons=(DecisionReadinessReason(DecisionReadinessReasonKind.SUBSTANTIAL_COVERAGE_REACHED),),
        stance_level=StanceLevel.INCREASE,
        stance_top_reason_code=StanceReasonCode.DECISION_SUPPORT_FAVORABLE,
        is_thesis_stale=False,
    )
    base.update(overrides)
    return SynthesisInputs(**base)


class TestActionMapping:
    def test_every_decision_support_level_maps_to_a_real_action(self):
        assert set(ACTION_BY_DECISION_SUPPORT_LEVEL.keys()) == set(DecisionSupportLevel)
        assert set(ACTION_BY_DECISION_SUPPORT_LEVEL.values()) == set(DecisionAction)

    def test_entry_supported_is_buy(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.ENTRY_SUPPORTED), generated_at=NOW)
        assert decision.action is DecisionAction.BUY

    def test_increase_supported_is_add(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.INCREASE_SUPPORTED), generated_at=NOW)
        assert decision.action is DecisionAction.ADD

    def test_thesis_intact_is_hold(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.THESIS_INTACT), generated_at=NOW)
        assert decision.action is DecisionAction.HOLD

    def test_reduction_supported_is_reduce(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.REDUCTION_SUPPORTED), generated_at=NOW)
        assert decision.action is DecisionAction.REDUCE

    def test_exit_supported_is_exit(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.EXIT_SUPPORTED), generated_at=NOW)
        assert decision.action is DecisionAction.EXIT

    def test_no_action_supported_is_wait(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.NO_ACTION_SUPPORTED), generated_at=NOW)
        assert decision.action is DecisionAction.WAIT

    def test_insufficient_evidence_is_no_decision(self):
        decision = synthesize_decision("c1", _inputs(decision_support_level=DecisionSupportLevel.INSUFFICIENT_EVIDENCE), generated_at=NOW)
        assert decision.action is DecisionAction.NO_DECISION


class TestQualifiers:
    def test_healthy_baseline_is_strong_decision(self):
        decision = synthesize_decision("c1", _inputs(), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert kinds == {DecisionQualifierKind.STRONG_DECISION}

    def test_blocked_readiness_is_decision_blocked(self):
        decision = synthesize_decision("c1", _inputs(readiness_status=DecisionReadinessStatus.BLOCKED), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.DECISION_BLOCKED in kinds
        assert DecisionQualifierKind.STRONG_DECISION not in kinds

    def test_avoid_decision_stance_is_also_decision_blocked(self):
        decision = synthesize_decision("c1", _inputs(stance_level=StanceLevel.AVOID_DECISION), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.DECISION_BLOCKED in kinds

    def test_unavailable_readiness_is_operationally_delayed(self):
        decision = synthesize_decision("c1", _inputs(readiness_status=DecisionReadinessStatus.UNAVAILABLE), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.OPERATIONALLY_DELAYED in kinds

    def test_evidence_limiting_blocker_is_evidence_limited(self):
        inputs = _inputs(
            readiness_status=DecisionReadinessStatus.WAITING,
            readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MISSING_THESIS_EVIDENCE, detail=3),),
        )
        decision = synthesize_decision("c1", inputs, generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.EVIDENCE_LIMITED in kinds

    def test_stale_thesis_is_temporary_decision(self):
        decision = synthesize_decision("c1", _inputs(is_thesis_stale=True), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.TEMPORARY_DECISION in kinds

    def test_almost_ready_is_careful_decision(self):
        decision = synthesize_decision("c1", _inputs(readiness_status=DecisionReadinessStatus.ALMOST_READY), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.CAREFUL_DECISION in kinds

    def test_review_stance_is_also_careful_decision(self):
        decision = synthesize_decision("c1", _inputs(stance_level=StanceLevel.REVIEW), generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.CAREFUL_DECISION in kinds

    def test_multiple_real_triggers_all_apply_together(self):
        inputs = _inputs(readiness_status=DecisionReadinessStatus.WAITING, is_thesis_stale=True)
        decision = synthesize_decision("c1", inputs, generated_at=NOW)
        kinds = {q.kind for q in decision.qualifiers}
        assert DecisionQualifierKind.TEMPORARY_DECISION in kinds
        assert DecisionQualifierKind.STRONG_DECISION not in kinds


class TestReasonsAndBlockers:
    def test_readiness_blockers_are_reused_verbatim(self):
        inputs = _inputs(
            readiness_status=DecisionReadinessStatus.WAITING,
            readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),),
        )
        decision = synthesize_decision("c1", inputs, generated_at=NOW)
        assert decision.blockers == (DecisionReason(DecisionReasonSource.READINESS_BLOCKER, "monitoring_pending"),)

    def test_stance_top_reason_is_prepended_as_a_supporting_reason(self):
        decision = synthesize_decision("c1", _inputs(), generated_at=NOW)
        assert decision.supporting_reasons[0] == DecisionReason(DecisionReasonSource.STANCE, "decision_support_favorable")

    def test_no_stance_produces_no_stance_reason(self):
        decision = synthesize_decision("c1", _inputs(stance_level=None, stance_top_reason_code=None), generated_at=NOW)
        assert not any(r.source is DecisionReasonSource.STANCE for r in decision.supporting_reasons)

    def test_change_trigger_is_the_first_blocker(self):
        inputs = _inputs(
            readiness_status=DecisionReadinessStatus.WAITING,
            readiness_blockers=(
                DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),
                DecisionBlocker(DecisionBlockerKind.COVERAGE_INCOMPLETE),
            ),
        )
        decision = synthesize_decision("c1", inputs, generated_at=NOW)
        assert decision.change_trigger == decision.blockers[0]

    def test_no_blockers_means_no_change_trigger(self):
        decision = synthesize_decision("c1", _inputs(), generated_at=NOW)
        assert decision.change_trigger is None


class TestSummarizeDecision:
    def test_primary_fields_are_the_first_entries(self):
        inputs = _inputs(
            readiness_status=DecisionReadinessStatus.WAITING,
            readiness_blockers=(DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING),),
        )
        decision = synthesize_decision("c1", inputs, generated_at=NOW)
        summary = summarize_decision(decision)
        assert summary.primary_blocker == decision.blockers[0]
        assert summary.primary_supporting_reason == decision.supporting_reasons[0]

    def test_no_qualifiers_means_no_primary_qualifier(self):
        inputs = _inputs(readiness_status=DecisionReadinessStatus.WAITING, decision_support_level=DecisionSupportLevel.THESIS_INTACT)
        decision = synthesize_decision("c1", inputs, generated_at=NOW)
        summary = summarize_decision(decision)
        assert summary.primary_qualifier is None


class TestCompareDecisions:
    def test_differing_qualifier_kinds_is_the_symmetric_difference(self):
        a = synthesize_decision("a", _inputs(), generated_at=NOW)
        b = synthesize_decision("b", _inputs(readiness_status=DecisionReadinessStatus.ALMOST_READY), generated_at=NOW)
        comparison = compare_decisions(a, b)
        assert DecisionQualifierKind.STRONG_DECISION in comparison.differing_qualifier_kinds
        assert DecisionQualifierKind.CAREFUL_DECISION in comparison.differing_qualifier_kinds

    def test_shared_blocker_codes_are_the_intersection(self):
        shared_blocker = DecisionBlocker(DecisionBlockerKind.MONITORING_PENDING)
        a = synthesize_decision(
            "a", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(shared_blocker,)), generated_at=NOW
        )
        b = synthesize_decision(
            "b", _inputs(readiness_status=DecisionReadinessStatus.WAITING, readiness_blockers=(shared_blocker,)), generated_at=NOW
        )
        comparison = compare_decisions(a, b)
        assert comparison.shared_blocker_codes == ("monitoring_pending",)

    def test_comparison_never_names_a_winner(self):
        """No field on `DecisionComparison` ever states a preferred
        side -- structural check that only `a`/`b` (both real, full
        decisions) and set-difference/intersection fields exist."""
        a = synthesize_decision("a", _inputs(), generated_at=NOW)
        b = synthesize_decision("b", _inputs(readiness_status=DecisionReadinessStatus.BLOCKED), generated_at=NOW)
        comparison = compare_decisions(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert field_names == {"a", "b", "differing_qualifier_kinds", "shared_blocker_codes", "shared_supporting_reason_codes"}


class TestDetectDecisionChange:
    def _decision(self, action: DecisionAction, qualifiers=()) -> InvestmentDecision:
        from atlas.alpha.investment_decision.models import DecisionQualifier

        return InvestmentDecision(
            case_id="c1",
            action=action,
            qualifiers=tuple(DecisionQualifier(k) for k in qualifiers),
            supporting_reasons=(),
            blockers=(),
            change_trigger=None,
            generated_at=NOW,
        )

    def test_no_previous_computation_produces_no_change(self):
        current = self._decision(DecisionAction.BUY)
        assert detect_decision_change(None, current, detected_at=NOW) is None

    def test_identical_action_and_qualifiers_produce_no_change(self):
        previous = self._decision(DecisionAction.HOLD, (DecisionQualifierKind.STRONG_DECISION,))
        current = self._decision(DecisionAction.HOLD, (DecisionQualifierKind.STRONG_DECISION,))
        assert detect_decision_change(previous, current, detected_at=NOW) is None

    def test_a_real_action_transition_is_reported(self):
        previous = self._decision(DecisionAction.HOLD)
        current = self._decision(DecisionAction.ADD)
        change = detect_decision_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_action is DecisionAction.HOLD
        assert change.current_action is DecisionAction.ADD

    def test_a_qualifier_only_change_is_reported_even_with_the_same_action(self):
        previous = self._decision(DecisionAction.HOLD, (DecisionQualifierKind.STRONG_DECISION,))
        current = self._decision(DecisionAction.HOLD, (DecisionQualifierKind.DECISION_BLOCKED,))
        change = detect_decision_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.previous_action == change.current_action
