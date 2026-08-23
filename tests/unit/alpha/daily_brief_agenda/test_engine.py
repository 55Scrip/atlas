"""Pure unit tests for `atlas.alpha.daily_brief_agenda.engine` -- the
deterministic priority mapping and per-ticker consolidation rules.
Real-persistence orchestration is covered by `test_service.py` instead,
mirroring `atlas.alpha.portfolio_fit`'s own division of labor.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.daily_brief_agenda.engine import (
    Signal,
    TickerContext,
    assumption_signal,
    build_agenda,
    business_quality_signal,
    case_condition_signal,
    change_intelligence_signal,
    concentration_signal,
    decision_explanation_signal,
    decision_reliability_signal,
    executive_change_signal,
    management_credibility_signal,
    portfolio_decision_signal,
    decision_memory_signal,
    decision_path_signal,
    evidence_gap_signal,
    investment_decision_signal,
    opportunity_cost_signal,
    portfolio_fit_signal,
    recommendation_conviction_signal,
    workflow_signal,
)
from atlas.alpha.daily_brief_agenda.models import AgendaGroup, AgendaItemKind, AgendaSource, PriorityLevel, SignalNature
from atlas.alpha.investment_case.business_quality_intelligence import BusinessQualityFindingKind
from atlas.alpha.investment_case.executive_change_intelligence import ExecutiveRoleCategory
from atlas.alpha.investment_case.management_credibility_intelligence import CredibilityFindingKind
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.investment_decision.models import DecisionAction, DecisionQualifierKind
from atlas.alpha.portfolio_fit.models import FitRating, FitTrend
from atlas.alpha.recommendation_conviction.models import RecommendationStability
from atlas.alpha.portfolio_intelligence.models import KeyFindingKind
from atlas.alpha.portfolio_status.models import AttentionCategory
from atlas.analysis_engine.investment_case_change import ThesisImpact

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestWorkflowSignal:
    def test_decision_without_outcome_is_critical(self):
        signal = workflow_signal(AttentionCategory.DECISION_WITHOUT_OUTCOME, "reason")
        assert signal.priority is PriorityLevel.CRITICAL
        assert signal.kind is AgendaItemKind.REVIEW_PORTFOLIO_POSITION

    def test_missing_case_is_high(self):
        assert workflow_signal(AttentionCategory.MISSING_CASE, "r").priority is PriorityLevel.HIGH

    def test_very_old_case_is_normal(self):
        assert workflow_signal(AttentionCategory.VERY_OLD_CASE, "r").priority is PriorityLevel.NORMAL


class TestCaseConditionSignal:
    def test_invalidation_satisfied_is_critical(self):
        signal = case_condition_signal("invalidation", "satisfied", "r", _NOW)
        assert signal is not None
        assert signal.priority is PriorityLevel.CRITICAL
        assert signal.kind is AgendaItemKind.EVALUATE_CASE_CONDITION

    def test_monitoring_satisfied_is_high(self):
        signal = case_condition_signal("monitoring", "satisfied", "r", _NOW)
        assert signal is not None
        assert signal.priority is PriorityLevel.HIGH

    def test_active_condition_produces_no_signal(self):
        assert case_condition_signal("monitoring", "active", "r", _NOW) is None

    def test_retired_condition_produces_no_signal(self):
        assert case_condition_signal("invalidation", "retired", "r", _NOW) is None

    def test_satisfied_condition_is_a_persistent_condition_with_the_real_since(self):
        """Fix Sprint 4: `since` is composed from the caller's own
        already-computed `CaseConditionView.updated_at`, never
        re-derived here -- this test confirms it passes straight
        through, byte-for-byte."""
        signal = case_condition_signal("monitoring", "satisfied", "r", _NOW)
        assert signal is not None
        assert signal.nature is SignalNature.PERSISTENT_CONDITION
        assert signal.since == _NOW


class TestAssumptionSignal:
    def test_invalidated_is_critical(self):
        signal = assumption_signal("invalidated", "r", _NOW)
        assert signal is not None
        assert signal.priority is PriorityLevel.CRITICAL

    def test_challenged_is_high(self):
        signal = assumption_signal("challenged", "r", _NOW)
        assert signal is not None
        assert signal.priority is PriorityLevel.HIGH

    def test_supported_produces_no_signal(self):
        assert assumption_signal("supported", "r", _NOW) is None

    def test_challenged_assumption_is_a_persistent_condition_with_the_real_since(self):
        signal = assumption_signal("challenged", "r", _NOW)
        assert signal is not None
        assert signal.nature is SignalNature.PERSISTENT_CONDITION
        assert signal.since == _NOW


class TestPortfolioFitSignal:
    def test_poor_holding_is_critical(self):
        signal = portfolio_fit_signal(FitRating.POOR, FitTrend.UNAVAILABLE, True, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.CRITICAL
        assert signal.kind is AgendaItemKind.REVIEW_PORTFOLIO_POSITION

    def test_poor_watchlist_uses_watchlist_kind(self):
        signal = portfolio_fit_signal(FitRating.POOR, FitTrend.UNAVAILABLE, False, "r")
        assert signal is not None
        assert signal.kind is AgendaItemKind.REVIEW_WATCHLIST_CANDIDATE

    def test_weak_and_declining_is_high(self):
        signal = portfolio_fit_signal(FitRating.WEAK, FitTrend.DECLINING, True, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.HIGH

    def test_weak_alone_is_normal(self):
        signal = portfolio_fit_signal(FitRating.WEAK, FitTrend.UNAVAILABLE, True, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.NORMAL

    def test_good_fit_watchlist_improving_is_a_low_priority_opportunity(self):
        signal = portfolio_fit_signal(FitRating.GOOD, FitTrend.IMPROVING, False, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.LOW
        assert signal.kind is AgendaItemKind.PORTFOLIO_OPPORTUNITY

    def test_good_fit_holding_improving_is_not_an_opportunity_kind(self):
        # Deliverable 6/9: an *existing* holding improving is informational,
        # never framed as a "portfolio opportunity" (that term means a
        # candidate worth considering, not a position already taken).
        signal = portfolio_fit_signal(FitRating.GOOD, FitTrend.IMPROVING, True, "r")
        assert signal is not None
        assert signal.kind is not AgendaItemKind.PORTFOLIO_OPPORTUNITY

    def test_excellent_fit_no_trend_produces_no_signal(self):
        assert portfolio_fit_signal(FitRating.EXCELLENT, FitTrend.UNAVAILABLE, True, "r") is None

    def test_neutral_fit_no_trend_produces_no_signal(self):
        assert portfolio_fit_signal(FitRating.NEUTRAL, FitTrend.UNAVAILABLE, True, "r") is None


class TestChangeIntelligenceSignal:
    def test_weakened_is_high(self):
        assert change_intelligence_signal(ThesisImpact.WEAKENED, "r").priority is PriorityLevel.HIGH

    def test_strengthened_is_low(self):
        assert change_intelligence_signal(ThesisImpact.STRENGTHENED, "r").priority is PriorityLevel.LOW

    def test_mixed_is_normal(self):
        assert change_intelligence_signal(ThesisImpact.MIXED, "r").priority is PriorityLevel.NORMAL


class TestConcentrationSignal:
    def test_high_concentration_is_high(self):
        signal = concentration_signal(KeyFindingKind.HIGH_CONCENTRATION, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.HIGH
        assert signal.kind is AgendaItemKind.PORTFOLIO_RISK

    def test_elevated_concentration_is_normal(self):
        signal = concentration_signal(KeyFindingKind.ELEVATED_CONCENTRATION, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.NORMAL

    def test_non_concentration_finding_produces_no_signal(self):
        assert concentration_signal(KeyFindingKind.MULTIPLE_MISSING_CASES, "r") is None


class TestEvidenceGapSignal:
    """Sprint 8, Deliverable 4: matches `derivePortfolioActions.ts`'s own
    "high" tier for a missing-evidence gap -- the one "Needs Your
    Attention" signal this engine previously had no equivalent for."""

    def test_missing_evidence_is_high(self):
        signal = evidence_gap_signal("r")
        assert signal.priority is PriorityLevel.HIGH
        assert signal.kind is AgendaItemKind.REVIEW_PORTFOLIO_POSITION
        assert signal.source is AgendaSource.PORTFOLIO_INTELLIGENCE


class TestExecutiveChangeSignal:
    """Product Intelligence Sprint 1 (Portfolio Intelligence Activation):
    a real leadership change, already computed by `executive_change_
    intelligence.py`, never a new detector."""

    def test_ceo_change_is_high(self):
        since = datetime(2026, 1, 1, tzinfo=timezone.utc)
        signal = executive_change_signal(ExecutiveRoleCategory.CEO, "r", since)
        assert signal.priority is PriorityLevel.HIGH
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE
        assert signal.source is AgendaSource.EXECUTIVE_CHANGE
        assert signal.nature is SignalNature.CHANGE_EVENT
        assert signal.since is since

    def test_cfo_change_is_normal(self):
        signal = executive_change_signal(ExecutiveRoleCategory.CFO, "r", None)
        assert signal.priority is PriorityLevel.NORMAL

    def test_board_director_change_is_low(self):
        signal = executive_change_signal(ExecutiveRoleCategory.BOARD_DIRECTOR, "r", None)
        assert signal.priority is PriorityLevel.LOW


class TestManagementCredibilitySignal:
    """Product Intelligence Sprint 1: only a real deterioration finding
    becomes an attention item -- a positive or neutral finding never
    does."""

    def test_inconsistent_follow_through_is_high(self):
        signal = management_credibility_signal(CredibilityFindingKind.INCONSISTENT_FOLLOW_THROUGH, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.HIGH
        assert signal.source is AgendaSource.MANAGEMENT_CREDIBILITY
        assert signal.nature is SignalNature.PERSISTENT_CONDITION

    def test_guidance_revised_downward_is_normal(self):
        signal = management_credibility_signal(CredibilityFindingKind.GUIDANCE_REVISED_DOWNWARD, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.NORMAL

    def test_consistent_follow_through_produces_no_signal(self):
        assert management_credibility_signal(CredibilityFindingKind.CONSISTENT_FOLLOW_THROUGH, "r") is None

    def test_mixed_follow_through_produces_no_signal(self):
        assert management_credibility_signal(CredibilityFindingKind.MIXED_FOLLOW_THROUGH, "r") is None

    def test_communication_shifted_produces_no_signal(self):
        assert management_credibility_signal(CredibilityFindingKind.COMMUNICATION_SHIFTED, "r") is None

    def test_insufficient_history_produces_no_signal(self):
        assert management_credibility_signal(CredibilityFindingKind.INSUFFICIENT_HISTORY, "r") is None


class TestBusinessQualitySignal:
    """Product Intelligence Sprint 1: only `WEAKENING_BUSINESS` becomes
    an attention item -- every other, genuinely positive or neutral
    finding never does."""

    def test_weakening_business_is_high(self):
        signal = business_quality_signal(BusinessQualityFindingKind.WEAKENING_BUSINESS, "r")
        assert signal is not None
        assert signal.priority is PriorityLevel.HIGH
        assert signal.source is AgendaSource.BUSINESS_QUALITY
        assert signal.nature is SignalNature.PERSISTENT_CONDITION

    def test_strengthening_business_produces_no_signal(self):
        assert business_quality_signal(BusinessQualityFindingKind.STRENGTHENING_BUSINESS, "r") is None

    def test_consistent_value_creation_produces_no_signal(self):
        assert business_quality_signal(BusinessQualityFindingKind.CONSISTENT_VALUE_CREATION, "r") is None

    def test_insufficient_history_produces_no_signal(self):
        assert business_quality_signal(BusinessQualityFindingKind.INSUFFICIENT_HISTORY, "r") is None


class TestInvestmentDecisionSignal:
    """Atlas Decision Layer Sprint 1, Deliverable 10: becoming Decision
    Blocked is the one elevated case, mirroring `_READINESS_CHANGE
    _PRIORITY`'s own "one elevated case, everything else ordinary"
    shape; every other transition is priced off the new action alone."""

    def test_becoming_decision_blocked_is_high_regardless_of_action(self):
        signal = investment_decision_signal(DecisionAction.HOLD, (DecisionQualifierKind.DECISION_BLOCKED,), "reason")
        assert signal.priority is PriorityLevel.HIGH
        assert signal.source is AgendaSource.INVESTMENT_DECISION
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE

    def test_an_actionable_transition_is_normal(self):
        for action in (DecisionAction.BUY, DecisionAction.ADD, DecisionAction.REDUCE, DecisionAction.EXIT):
            signal = investment_decision_signal(action, (), "reason")
            assert signal.priority is PriorityLevel.NORMAL

    def test_settling_into_hold_or_wait_is_low(self):
        for action in (DecisionAction.HOLD, DecisionAction.WAIT, DecisionAction.NO_DECISION):
            signal = investment_decision_signal(action, (), "reason")
            assert signal.priority is PriorityLevel.LOW


class TestRecommendationConvictionSignal:
    """Atlas Decision Layer Sprint 2, Deliverable 10: becoming
    Operationally Blocked is the one elevated case; every other real
    strength/stability transition is ordinary-priority news, never
    inflated."""

    def test_becoming_operationally_blocked_is_high(self):
        signal = recommendation_conviction_signal(RecommendationStability.OPERATIONALLY_BLOCKED, "reason")
        assert signal.priority is PriorityLevel.HIGH
        assert signal.source is AgendaSource.RECOMMENDATION_CONVICTION
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE

    def test_every_other_stability_is_normal(self):
        for stability in (
            RecommendationStability.STABLE,
            RecommendationStability.FRAGILE,
            RecommendationStability.WAITING_FOR_EVIDENCE,
            RecommendationStability.EVIDENCE_LIMITED,
        ):
            signal = recommendation_conviction_signal(stability, "reason")
            assert signal.priority is PriorityLevel.NORMAL


class TestDecisionPathSignal:
    """Atlas Decision Layer Sprint 3, Deliverable 10: becoming
    `NOT_REACHABLE` (no real path forward exists today) is the one
    elevated case; every other real endpoint transition is
    ordinary-priority news, never inflated."""

    def test_becoming_not_reachable_is_high(self):
        signal = decision_path_signal(FinalReachableState.NOT_REACHABLE, "reason")
        assert signal.priority is PriorityLevel.HIGH
        assert signal.source is AgendaSource.DECISION_PATH
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE

    def test_every_other_final_state_is_normal(self):
        for state in (
            FinalReachableState.ALREADY_REACHED,
            FinalReachableState.FULLY_REACHABLE,
            FinalReachableState.PARTIALLY_REACHABLE,
        ):
            signal = decision_path_signal(state, "reason")
            assert signal.priority is PriorityLevel.NORMAL


class TestOpportunityCostSignal:
    """Atlas Decision Layer Sprint 4, Deliverable 10: deliberately
    never elevated -- a real alternative-set change is genuine,
    informational news, never itself an alarm."""

    def test_always_normal(self):
        signal = opportunity_cost_signal("reason")
        assert signal.priority is PriorityLevel.NORMAL
        assert signal.source is AgendaSource.OPPORTUNITY_COST
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE


class TestDecisionMemorySignal:
    """Atlas Decision Layer Sprint 5, Deliverable 10: deliberately
    never elevated -- a recorded change to the decision itself is
    durable, factual news, never itself an alarm (the alarm, if any,
    already fired from the layer whose own change is being recorded)."""

    def test_always_normal(self):
        signal = decision_memory_signal("reason")
        assert signal.priority is PriorityLevel.NORMAL
        assert signal.source is AgendaSource.DECISION_MEMORY
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE


class TestDecisionExplanationSignal:
    """Atlas Decision Layer Sprint 6, Deliverable 10: deliberately
    never elevated -- a change to why the decision stands as it does
    is genuine, informational news, never itself an alarm (the alarm,
    if any, already fired from the layer whose own change is being
    explained)."""

    def test_always_normal(self):
        signal = decision_explanation_signal("reason")
        assert signal.priority is PriorityLevel.NORMAL
        assert signal.source is AgendaSource.DECISION_EXPLANATION
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE


class TestDecisionReliabilitySignal:
    """Atlas Decision Layer Sprint 7, Deliverable 11: deliberately
    never elevated -- a change to how trustworthy the decision is is
    genuine, informational news, never itself an alarm (the alarm, if
    any, already fired from the layer whose own underlying fact is
    being reflected)."""

    def test_always_normal(self):
        signal = decision_reliability_signal("reason")
        assert signal.priority is PriorityLevel.NORMAL
        assert signal.source is AgendaSource.DECISION_RELIABILITY
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE


class TestPortfolioDecisionSignal:
    """Atlas Decision Layer Sprint 8, Deliverable 11: deliberately
    never elevated -- a change to what a decision means for the
    portfolio is genuine, informational news, never itself a new
    alarm (the alarm, if any, already fired from the layer whose own
    underlying fact is being reflected)."""

    def test_always_normal(self):
        signal = portfolio_decision_signal("reason")
        assert signal.priority is PriorityLevel.NORMAL
        assert signal.source is AgendaSource.PORTFOLIO_DECISION
        assert signal.kind is AgendaItemKind.REVIEW_INVESTMENT_CASE


class TestConsolidation:
    """Deliverable 8 (noise reduction): one agenda item per ticker, no
    matter how many real signals fired for it."""

    def test_multiple_signals_for_one_ticker_produce_exactly_one_item(self):
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            change_intelligence_signal(ThesisImpact.WEAKENED, "thesis weakened"),
            Signal(
                PriorityLevel.CRITICAL,
                AgendaItemKind.EVALUATE_CASE_CONDITION,
                AgendaSource.CASE_CONDITION,
                "condition satisfied",
                SignalNature.PERSISTENT_CONDITION,
            ),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_the_highest_priority_signal_decides_the_items_own_kind_and_headline(self):
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            change_intelligence_signal(ThesisImpact.WEAKENED, "thesis weakened"),
            Signal(
                PriorityLevel.CRITICAL,
                AgendaItemKind.EVALUATE_CASE_CONDITION,
                AgendaSource.CASE_CONDITION,
                "condition satisfied",
                SignalNature.PERSISTENT_CONDITION,
            ),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        item = agenda.items[0]
        assert item.priority is PriorityLevel.CRITICAL
        assert item.kind is AgendaItemKind.EVALUATE_CASE_CONDITION
        assert item.headline == "condition satisfied"

    def test_every_real_signals_reason_is_preserved_even_when_it_did_not_win(self):
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            change_intelligence_signal(ThesisImpact.WEAKENED, "thesis weakened"),
            Signal(
                PriorityLevel.CRITICAL,
                AgendaItemKind.EVALUATE_CASE_CONDITION,
                AgendaSource.CASE_CONDITION,
                "condition satisfied",
                SignalNature.PERSISTENT_CONDITION,
            ),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert "condition satisfied" in agenda.items[0].reason
        assert "thesis weakened" in agenda.items[0].reason

    def test_a_ticker_with_no_real_signal_produces_no_item(self):
        context = TickerContext("AAPL", "case-aapl", True, None)
        agenda = build_agenda({"AAPL": (context, [])}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert agenda.items == ()

    def test_tie_break_prefers_case_condition_over_change_intelligence_at_equal_priority(self):
        # Both are engineered to the same priority (HIGH) to isolate the
        # tie-break rule itself, not the priority mapping.
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.HIGH,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(
                PriorityLevel.HIGH,
                AgendaItemKind.EVALUATE_CASE_CONDITION,
                AgendaSource.CASE_CONDITION,
                "condition satisfied",
                SignalNature.PERSISTENT_CONDITION,
            ),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert agenda.items[0].source is AgendaSource.CASE_CONDITION

    def test_decision_readiness_signal_never_raises_on_tie_break(self):
        """Live Verification finding (Atlas Intelligence Sprint 11,
        Deliverable 10/15) -- `_SOURCE_TIE_RANK` originally had no
        entry for the newly-added `AgendaSource.DECISION_READINESS`,
        so any ticker with a Decision Readiness signal competing
        against another equal-priority signal raised a real `KeyError`
        in production (confirmed live against the real backend)."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.HIGH,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.HIGH, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_READINESS, "readiness changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_investment_decision_signal_never_raises_on_tie_break(self):
        """Learned directly from `test_decision_readiness_signal_never
        _raises_on_tie_break` above (Sprint 11's own live-verification
        bug) -- `_SOURCE_TIE_RANK` must carry an entry for
        `AgendaSource.INVESTMENT_DECISION` from the start, checked here
        rather than discovered live."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.HIGH,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.HIGH, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.INVESTMENT_DECISION, "decision changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_recommendation_conviction_signal_never_raises_on_tie_break(self):
        """Learned directly from the same two prior sprints' own
        live-verification bugs (Sprint 11, then again confirmed as a
        deliberate regression test in Sprint 1 of this program) --
        `_SOURCE_TIE_RANK` must carry an entry for
        `AgendaSource.RECOMMENDATION_CONVICTION` from the start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.RECOMMENDATION_CONVICTION, "conviction changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_decision_path_signal_never_raises_on_tie_break(self):
        """Learned directly from the same repeated lesson across
        Sprints 11, 1, and 2 of this program -- `_SOURCE_TIE_RANK`
        must carry an entry for `AgendaSource.DECISION_PATH` from the
        start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_PATH, "path changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_opportunity_cost_signal_never_raises_on_tie_break(self):
        """Learned directly from the same repeated lesson across
        Sprints 11, 1, 2, and 3 of this program -- `_SOURCE_TIE_RANK`
        must carry an entry for `AgendaSource.OPPORTUNITY_COST` from
        the start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.OPPORTUNITY_COST, "alternatives changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_decision_memory_signal_never_raises_on_tie_break(self):
        """Learned directly from the same repeated lesson across
        Sprints 11, 1, 2, 3, and 4 of this program -- `_SOURCE_TIE_RANK`
        must carry an entry for `AgendaSource.DECISION_MEMORY` from
        the start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_MEMORY, "recorded decision changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_decision_explanation_signal_never_raises_on_tie_break(self):
        """Learned directly from the same repeated lesson across
        Sprints 11, 1, 2, 3, 4, and 5 of this program --
        `_SOURCE_TIE_RANK` must carry an entry for
        `AgendaSource.DECISION_EXPLANATION` from the start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_EXPLANATION, "explanation changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_decision_reliability_signal_never_raises_on_tie_break(self):
        """Learned directly from the same repeated lesson across
        Sprints 11, 1, 2, 3, 4, 5, and 6 of this program --
        `_SOURCE_TIE_RANK` must carry an entry for
        `AgendaSource.DECISION_RELIABILITY` from the start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.DECISION_RELIABILITY, "reliability changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_portfolio_decision_signal_never_raises_on_tie_break(self):
        """Learned directly from the same repeated lesson across
        Sprints 11, 1, 2, 3, 4, 5, 6, and 7 of this program --
        `_SOURCE_TIE_RANK` must carry an entry for
        `AgendaSource.PORTFOLIO_DECISION` from the start."""
        context = TickerContext("AAPL", "case-aapl", True, None)
        signals = [
            Signal(
                PriorityLevel.NORMAL,
                AgendaItemKind.REVIEW_INVESTMENT_CASE,
                AgendaSource.CHANGE_INTELLIGENCE,
                "thesis weakened",
                SignalNature.CHANGE_EVENT,
            ),
            Signal(PriorityLevel.NORMAL, AgendaItemKind.REVIEW_INVESTMENT_CASE, AgendaSource.PORTFOLIO_DECISION, "portfolio decision changed", SignalNature.CHANGE_EVENT),
        ]
        agenda = build_agenda({"AAPL": (context, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert len(agenda.items) == 1

    def test_holding_lands_in_portfolio_group_watchlist_only_in_watchlist_group(self):
        holding_ctx = TickerContext("AAPL", "case-aapl", True, None)
        watchlist_ctx = TickerContext("NVDA", "case-nvda", False, None)
        signal = change_intelligence_signal(ThesisImpact.WEAKENED, "r")
        agenda = build_agenda(
            {"AAPL": (holding_ctx, [signal]), "NVDA": (watchlist_ctx, [signal])},
            [],
            holdings_count=1,
            cash_weight_percent=None,
            concentration_level=None,
            now=_NOW,
        )
        by_ticker = {i.ticker: i for i in agenda.items}
        assert by_ticker["AAPL"].group is AgendaGroup.PORTFOLIO
        assert by_ticker["NVDA"].group is AgendaGroup.WATCHLIST


class TestOrdering:
    def test_items_sort_by_priority_critical_first(self):
        low_ctx = TickerContext("LOW", "case-low", True, None)
        crit_ctx = TickerContext("CRIT", "case-crit", True, None)
        agenda = build_agenda(
            {
                "LOW": (low_ctx, [change_intelligence_signal(ThesisImpact.STRENGTHENED, "r")]),
                "CRIT": (crit_ctx, [portfolio_fit_signal(FitRating.POOR, FitTrend.UNAVAILABLE, True, "r")]),
            },
            [],
            holdings_count=2,
            cash_weight_percent=None,
            concentration_level=None,
            now=_NOW,
        )
        assert [i.ticker for i in agenda.items] == ["CRIT", "LOW"]

    def test_equal_priority_ties_break_alphabetically_by_ticker(self):
        a_ctx = TickerContext("BBB", "case-bbb", True, None)
        b_ctx = TickerContext("AAA", "case-aaa", True, None)
        signal_factory = lambda: change_intelligence_signal(ThesisImpact.WEAKENED, "r")  # noqa: E731
        agenda = build_agenda(
            {"BBB": (a_ctx, [signal_factory()]), "AAA": (b_ctx, [signal_factory()])},
            [],
            holdings_count=2,
            cash_weight_percent=None,
            concentration_level=None,
            now=_NOW,
        )
        assert [i.ticker for i in agenda.items] == ["AAA", "BBB"]

    def test_same_input_always_produces_the_same_order(self):
        ctx = TickerContext("AAPL", "case-aapl", True, None)
        signals = [change_intelligence_signal(ThesisImpact.WEAKENED, "r")]
        first = build_agenda({"AAPL": (ctx, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        second = build_agenda({"AAPL": (ctx, signals)}, [], holdings_count=1, cash_weight_percent=None, concentration_level=None, now=_NOW)
        assert first.items == second.items


class TestSummary:
    def test_critical_and_high_counts_are_derived_from_the_final_items_not_passed_in(self):
        crit_ctx = TickerContext("A", "case-a", True, None)
        high_ctx = TickerContext("B", "case-b", True, None)
        agenda = build_agenda(
            {
                "A": (crit_ctx, [portfolio_fit_signal(FitRating.POOR, FitTrend.UNAVAILABLE, True, "r")]),
                "B": (high_ctx, [change_intelligence_signal(ThesisImpact.WEAKENED, "r")]),
            },
            [],
            holdings_count=2,
            cash_weight_percent=12.5,
            concentration_level="Elevated",
            now=_NOW,
        )
        assert agenda.summary.critical_count == 1
        assert agenda.summary.high_count == 1
        assert agenda.summary.holdings_count == 2
        assert agenda.summary.cash_weight_percent == 12.5
        assert agenda.summary.concentration_level == "Elevated"

    def test_no_signals_at_all_is_an_honest_empty_agenda(self):
        agenda = build_agenda({}, [], holdings_count=3, cash_weight_percent=10.0, concentration_level="Low", now=_NOW)
        assert agenda.items == ()
        assert agenda.summary.critical_count == 0
        assert agenda.summary.high_count == 0
        assert agenda.summary.watchlist_opportunity_count == 0
