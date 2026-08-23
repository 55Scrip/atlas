"""Tests for `atlas.alpha.opportunity_cost.engine` -- alternative
construction (grounding, ordering, the "never invent" gates),
the pairwise comparison wrapper, and the summary/change-detection/
portfolio-breakdown helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_path.models import (
    DecisionPath,
    DecisionStep,
    DependencyReference,
    DependencySource,
    FinalReachableState,
    ReachabilityStatus,
    RequiredProgressKind,
)
from atlas.alpha.investment_decision.models import DecisionAction, DecisionReason, DecisionReasonSource
from atlas.alpha.opportunity_cost.engine import (
    OtherCaseSummary,
    build_alternative_comparison,
    build_alternatives,
    build_opportunity_cost,
    build_portfolio_opportunity_cost_breakdown,
    detect_opportunity_cost_change,
    summarize_opportunity_cost,
)
from atlas.alpha.opportunity_cost.models import (
    AlternativeKind,
    AlternativeReason,
    AlternativeReasonSource,
    DecisionAlternative,
    DecisionTradeoff,
    OpportunityCost,
)
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationConviction, RecommendationStability

NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _path(case_id: str = "current", steps: tuple[DecisionStep, ...] = (), final_state=FinalReachableState.ALREADY_REACHED) -> DecisionPath:
    return DecisionPath(
        case_id=case_id,
        current_action=DecisionAction.HOLD,
        current_strength=ConvictionStrength.MODERATE,
        steps=steps,
        immediate_blocker=steps[0] if steps else None,
        next_achievable_improvement=next((s for s in steps if s.reachability is ReachabilityStatus.REACHABLE), None),
        final_reachable_state=final_state,
        generated_at=NOW,
    )


def _conviction(case_id: str = "current", strength=ConvictionStrength.MODERATE) -> RecommendationConviction:
    return RecommendationConviction(
        case_id=case_id,
        action=DecisionAction.HOLD,
        strength=strength,
        stability=RecommendationStability.STABLE,
        supporting_reasons=(),
        limiting_reasons=(),
        strengthening_trigger=None,
        generated_at=NOW,
    )


def _decision_reason(code: str = "decision_support_favorable") -> DecisionReason:
    return DecisionReason(source=DecisionReasonSource.STANCE, code=code)


class TestBuildAlternatives:
    def test_other_holding_with_add_action_becomes_increase_existing_holding(self):
        others = (
            OtherCaseSummary("o1", "MSFT", is_holding=True, action=DecisionAction.ADD, top_reason=_decision_reason(), strength=ConvictionStrength.STRONG),
        )
        alternatives = build_alternatives(DecisionAction.HOLD, (), _path(), others)
        matches = [a for a in alternatives if a.case_id == "o1"]
        assert len(matches) == 1
        assert matches[0].kind is AlternativeKind.INCREASE_EXISTING_HOLDING
        assert matches[0].action is DecisionAction.ADD
        assert matches[0].strength is ConvictionStrength.STRONG

    def test_other_watchlist_with_buy_action_becomes_open_new_position(self):
        others = (
            OtherCaseSummary("o1", "NVDA", is_holding=False, action=DecisionAction.BUY, top_reason=_decision_reason(), strength=ConvictionStrength.VERY_STRONG),
        )
        alternatives = build_alternatives(DecisionAction.HOLD, (), _path(), others)
        matches = [a for a in alternatives if a.case_id == "o1"]
        assert matches[0].kind is AlternativeKind.OPEN_NEW_POSITION

    def test_other_case_with_hold_action_is_never_an_alternative(self):
        others = (OtherCaseSummary("o1", "MSFT", is_holding=True, action=DecisionAction.HOLD, top_reason=_decision_reason(), strength=None),)
        alternatives = build_alternatives(DecisionAction.HOLD, (), _path(), others)
        assert not any(a.case_id == "o1" for a in alternatives)

    def test_other_case_with_no_top_reason_is_never_an_alternative(self):
        others = (OtherCaseSummary("o1", "MSFT", is_holding=True, action=DecisionAction.ADD, top_reason=None, strength=None),)
        alternatives = build_alternatives(DecisionAction.HOLD, (), _path(), others)
        assert not any(a.case_id == "o1" for a in alternatives)

    def test_wait_and_keep_cash_grounded_in_the_immediate_blocker_when_present(self):
        step = DecisionStep(DependencyReference(DependencySource.READINESS_BLOCKER, "missing_thesis_evidence"), RequiredProgressKind.EVIDENCE, ReachabilityStatus.REACHABLE)
        alternatives = build_alternatives(DecisionAction.HOLD, (), _path(steps=(step,), final_state=FinalReachableState.FULLY_REACHABLE), ())
        wait = next(a for a in alternatives if a.kind is AlternativeKind.WAIT)
        assert wait.reason == AlternativeReason(AlternativeReasonSource.READINESS_BLOCKER, "missing_thesis_evidence")
        keep_cash = next(a for a in alternatives if a.kind is AlternativeKind.KEEP_CASH)
        assert keep_cash.reason == wait.reason

    def test_wait_grounded_in_top_supporting_reason_when_no_blocker(self):
        reason = _decision_reason("confidence_established")
        alternatives = build_alternatives(DecisionAction.HOLD, (reason,), _path(), ())
        wait = next(a for a in alternatives if a.kind is AlternativeKind.WAIT)
        assert wait.reason == AlternativeReason(AlternativeReasonSource.STANCE, "confidence_established")

    def test_no_alternatives_at_all_when_nothing_grounds_them(self):
        alternatives = build_alternatives(DecisionAction.BUY, (), _path(), ())
        assert alternatives == ()

    def test_no_action_present_only_for_hold_wait_or_no_decision(self):
        reason = _decision_reason()
        for action in (DecisionAction.HOLD, DecisionAction.WAIT, DecisionAction.NO_DECISION):
            alternatives = build_alternatives(action, (reason,), _path(), ())
            assert any(a.kind is AlternativeKind.NO_ACTION for a in alternatives)

    def test_no_action_absent_for_buy_add_reduce_exit(self):
        reason = _decision_reason()
        for action in (DecisionAction.BUY, DecisionAction.ADD, DecisionAction.REDUCE, DecisionAction.EXIT):
            alternatives = build_alternatives(action, (reason,), _path(), ())
            assert not any(a.kind is AlternativeKind.NO_ACTION for a in alternatives)

    def test_order_is_competing_cases_first_then_wait_keep_cash_no_action(self):
        others = (OtherCaseSummary("o1", "MSFT", is_holding=True, action=DecisionAction.ADD, top_reason=_decision_reason(), strength=None),)
        alternatives = build_alternatives(DecisionAction.HOLD, (_decision_reason(),), _path(), others)
        kinds = [a.kind for a in alternatives]
        assert kinds == [
            AlternativeKind.INCREASE_EXISTING_HOLDING,
            AlternativeKind.WAIT,
            AlternativeKind.KEEP_CASH,
            AlternativeKind.NO_ACTION,
        ]


class TestBuildAlternativeComparison:
    def test_reuses_conviction_and_path_comparisons_verbatim(self):
        current_conviction = _conviction("current", ConvictionStrength.STRONG)
        other_conviction = _conviction("other", ConvictionStrength.WEAK)
        current_path = _path("current")
        other_path = _path("other")
        comparison = build_alternative_comparison(current_conviction, other_conviction, current_path, other_path)
        assert comparison.conviction.stronger_case_id == "current"
        assert comparison.conviction.a is current_conviction
        assert comparison.path.a is current_path

    def test_more_dependency_blocked_case_id_from_real_step_counts(self):
        dependency_step = DecisionStep(DependencyReference(DependencySource.READINESS_BLOCKER, "critical_dependency_unresolved"), RequiredProgressKind.DEPENDENCY, ReachabilityStatus.REACHABLE)
        current_path = _path("current", steps=(dependency_step,), final_state=FinalReachableState.FULLY_REACHABLE)
        other_path = _path("other")
        comparison = build_alternative_comparison(_conviction("current"), _conviction("other"), current_path, other_path)
        assert comparison.more_dependency_blocked_case_id == "current"

    def test_tie_in_dependency_steps_is_none(self):
        comparison = build_alternative_comparison(_conviction("current"), _conviction("other"), _path("current"), _path("other"))
        assert comparison.more_dependency_blocked_case_id is None


class TestSummarizeOpportunityCost:
    def test_primary_is_first_tradeoff(self):
        alternative = DecisionAlternative(AlternativeKind.WAIT, None, None, None, None, AlternativeReason(AlternativeReasonSource.STANCE, "x"))
        opportunity_cost = build_opportunity_cost("c1", DecisionAction.HOLD, (DecisionTradeoff(alternative, None),), generated_at=NOW)
        summary = summarize_opportunity_cost(opportunity_cost)
        assert summary.primary_alternative == alternative
        assert summary.alternative_count == 1

    def test_no_tradeoffs_means_no_primary(self):
        opportunity_cost = build_opportunity_cost("c1", DecisionAction.BUY, (), generated_at=NOW)
        summary = summarize_opportunity_cost(opportunity_cost)
        assert summary.primary_alternative is None
        assert summary.alternative_count == 0


def _oc(case_id: str, tradeoffs: tuple[DecisionTradeoff, ...]) -> OpportunityCost:
    return build_opportunity_cost(case_id, DecisionAction.HOLD, tradeoffs, generated_at=NOW)


def _alt(kind: AlternativeKind, case_id: str | None = None, strength=None) -> DecisionAlternative:
    return DecisionAlternative(kind, case_id, case_id, None, strength, AlternativeReason(AlternativeReasonSource.STANCE, "x"))


class TestDetectOpportunityCostChange:
    def test_no_previous_computation_produces_no_change(self):
        current = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.WAIT), None),))
        assert detect_opportunity_cost_change(None, current, detected_at=NOW) is None

    def test_identical_alternatives_produce_no_change(self):
        previous = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.WAIT), None),))
        current = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.WAIT), None),))
        assert detect_opportunity_cost_change(previous, current, detected_at=NOW) is None

    def test_a_new_alternative_is_reported(self):
        previous = _oc("c1", ())
        current = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1"), None),))
        change = detect_opportunity_cost_change(previous, current, detected_at=NOW)
        assert change is not None
        assert len(change.new_alternatives) == 1
        assert change.new_alternatives[0].case_id == "o1"

    def test_a_disappeared_alternative_is_reported(self):
        previous = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1"), None),))
        current = _oc("c1", ())
        change = detect_opportunity_cost_change(previous, current, detected_at=NOW)
        assert change is not None
        assert len(change.disappeared_alternatives) == 1

    def test_a_strengthened_alternative_is_reported(self):
        previous = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1", ConvictionStrength.WEAK), None),))
        current = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1", ConvictionStrength.STRONG), None),))
        change = detect_opportunity_cost_change(previous, current, detected_at=NOW)
        assert change is not None
        assert len(change.strengthened_alternatives) == 1
        assert change.weakened_alternatives == ()

    def test_a_weakened_alternative_is_reported(self):
        previous = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1", ConvictionStrength.STRONG), None),))
        current = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1", ConvictionStrength.WEAK), None),))
        change = detect_opportunity_cost_change(previous, current, detected_at=NOW)
        assert change is not None
        assert len(change.weakened_alternatives) == 1

    def test_primary_alternative_changed_flag(self):
        previous = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.WAIT), None),))
        current = _oc("c1", (DecisionTradeoff(_alt(AlternativeKind.OPEN_NEW_POSITION, "o1"), None),))
        change = detect_opportunity_cost_change(previous, current, detected_at=NOW)
        assert change is not None
        assert change.primary_alternative_changed is True


class TestPortfolioOpportunityCostBreakdown:
    def test_buckets_correctly(self):
        buy_oc = _oc("h1", ())
        buy_oc = build_opportunity_cost("h1", DecisionAction.BUY, (), generated_at=NOW)
        wait_oc = build_opportunity_cost("h2", DecisionAction.HOLD, (DecisionTradeoff(_alt(AlternativeKind.WAIT), None),), generated_at=NOW)
        no_action_oc = build_opportunity_cost("h3", DecisionAction.HOLD, (DecisionTradeoff(_alt(AlternativeKind.NO_ACTION), None),), generated_at=NOW)
        items = (("AAPL", buy_oc), ("MSFT", wait_oc), ("NVDA", no_action_oc))
        breakdown = build_portfolio_opportunity_cost_breakdown(items, ("GOOGL",))
        assert breakdown.holdings_competing_for_capital == ("AAPL",)
        assert breakdown.waiting_preferable == ("MSFT",)
        assert breakdown.no_action_appropriate == ("NVDA",)
        assert breakdown.watchlist_competing_with_holdings == ("GOOGL",)

    def test_a_holding_with_both_wait_and_no_action_appears_in_both_buckets(self):
        """Live-verification finding: `build_alternatives` always
        constructs `WAIT` before `NO_ACTION` when both are grounded
        (its own fixed order), so checking only `tradeoffs[0]` left
        `no_action_appropriate` structurally near-empty -- any holding
        where "no action needed" is genuinely true almost always has a
        real `WAIT` grounding too. The two facts are not mutually
        exclusive in reality and must not be treated as such here."""
        both_oc = build_opportunity_cost(
            "h1",
            DecisionAction.HOLD,
            (DecisionTradeoff(_alt(AlternativeKind.WAIT), None), DecisionTradeoff(_alt(AlternativeKind.KEEP_CASH), None), DecisionTradeoff(_alt(AlternativeKind.NO_ACTION), None)),
            generated_at=NOW,
        )
        breakdown = build_portfolio_opportunity_cost_breakdown((("MSFT", both_oc),), ())
        assert breakdown.waiting_preferable == ("MSFT",)
        assert breakdown.no_action_appropriate == ("MSFT",)
