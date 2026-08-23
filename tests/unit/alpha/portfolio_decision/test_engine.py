"""Pure unit tests for `atlas.alpha.portfolio_decision.engine` --
classification, capital competition, comparison, and change detection.
No I/O; every input is a hand-built domain object."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.decision_explanation.models import ExplanationReferenceKind
from atlas.alpha.decision_reliability.models import ReliabilityLevel
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind, AlternativeReason, AlternativeReasonSource, DecisionAlternative
from atlas.alpha.portfolio_decision.engine import (
    build_capital_competition,
    build_portfolio_decision,
    build_portfolio_synthesis_breakdown,
    classify_portfolio_decision,
    compare_portfolio_decisions,
    detect_portfolio_decision_change,
    summarize_portfolio_decision,
)
from atlas.alpha.portfolio_decision.models import PortfolioDecisionCategory, PortfolioDecisionReasonSource
from atlas.alpha.portfolio_fit.models import FitRating
from atlas.domains.portfolio.models import ConcentrationLevel

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
_CASE_ID = "case-1"


def _alt(kind: AlternativeKind, case_id: str | None = "other-case") -> DecisionAlternative:
    return DecisionAlternative(
        kind=kind,
        case_id=case_id if kind in (AlternativeKind.INCREASE_EXISTING_HOLDING, AlternativeKind.OPEN_NEW_POSITION) else None,
        ticker="OTHER" if case_id is not None and kind in (AlternativeKind.INCREASE_EXISTING_HOLDING, AlternativeKind.OPEN_NEW_POSITION) else None,
        action=DecisionAction.BUY if kind in (AlternativeKind.INCREASE_EXISTING_HOLDING, AlternativeKind.OPEN_NEW_POSITION) else None,
        strength=None,
        reason=AlternativeReason(AlternativeReasonSource.STANCE, "some_reason"),
    )


def _build(
    *,
    action: DecisionAction = DecisionAction.HOLD,
    reliability_level: ReliabilityLevel = ReliabilityLevel.HIGH,
    is_existing_holding: bool = True,
    current_weight_percent: float | None = 10.0,
    is_largest_position: bool = False,
    allocation_rating: FitRating | None = FitRating.NEUTRAL,
    portfolio_concentration_level: ConcentrationLevel = ConcentrationLevel.LOW,
    alternatives: tuple[DecisionAlternative, ...] = (),
    large_unallocated: bool = False,
):
    return build_portfolio_decision(
        _CASE_ID,
        action=action,
        reliability_level=reliability_level,
        is_existing_holding=is_existing_holding,
        current_weight_percent=current_weight_percent,
        is_largest_position=is_largest_position,
        allocation_rating=allocation_rating,
        portfolio_concentration_level=portfolio_concentration_level,
        concentration_findings_for_ticker=(),
        large_unallocated=large_unallocated,
        alternatives=alternatives,
        generated_at=_NOW,
    )


class TestClassifyPortfolioDecision:
    def test_unknown_reliability_is_always_unknown_regardless_of_other_inputs(self):
        category = classify_portfolio_decision(DecisionAction.BUY, ReliabilityLevel.UNKNOWN, True, True)
        assert category is PortfolioDecisionCategory.UNKNOWN

    def test_unavailable_reliability_is_always_operationally_limited(self):
        category = classify_portfolio_decision(DecisionAction.BUY, ReliabilityLevel.UNAVAILABLE, False, False)
        assert category is PortfolioDecisionCategory.OPERATIONALLY_LIMITED

    def test_buy_on_an_overweight_holding_conflicts_with_portfolio(self):
        category = classify_portfolio_decision(DecisionAction.BUY, ReliabilityLevel.HIGH, True, False)
        assert category is PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO

    def test_add_on_an_overweight_holding_conflicts_with_portfolio(self):
        category = classify_portfolio_decision(DecisionAction.ADD, ReliabilityLevel.HIGH, True, False)
        assert category is PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO

    def test_reduce_on_an_overweight_holding_supports_portfolio(self):
        category = classify_portfolio_decision(DecisionAction.REDUCE, ReliabilityLevel.HIGH, True, False)
        assert category is PortfolioDecisionCategory.SUPPORTS_PORTFOLIO

    def test_exit_on_an_overweight_holding_supports_portfolio(self):
        category = classify_portfolio_decision(DecisionAction.EXIT, ReliabilityLevel.HIGH, True, False)
        assert category is PortfolioDecisionCategory.SUPPORTS_PORTFOLIO

    def test_buy_with_real_capital_competition_requires_review(self):
        category = classify_portfolio_decision(DecisionAction.BUY, ReliabilityLevel.HIGH, False, True)
        assert category is PortfolioDecisionCategory.REQUIRES_REVIEW

    def test_hold_with_no_tension_is_neutral(self):
        category = classify_portfolio_decision(DecisionAction.HOLD, ReliabilityLevel.HIGH, False, False)
        assert category is PortfolioDecisionCategory.NEUTRAL

    def test_buy_with_no_overweight_and_no_competition_is_neutral(self):
        category = classify_portfolio_decision(DecisionAction.BUY, ReliabilityLevel.HIGH, False, False)
        assert category is PortfolioDecisionCategory.NEUTRAL


class TestBuildCapitalCompetition:
    def test_increase_existing_holding_is_a_real_competitor(self):
        alt = _alt(AlternativeKind.INCREASE_EXISTING_HOLDING)
        competition = build_capital_competition(_CASE_ID, (alt,))
        assert competition.competing_alternatives == (alt,)
        assert competition.non_competing_alternatives == ()

    def test_open_new_position_is_a_real_competitor(self):
        alt = _alt(AlternativeKind.OPEN_NEW_POSITION)
        competition = build_capital_competition(_CASE_ID, (alt,))
        assert competition.competing_alternatives == (alt,)

    def test_wait_keep_cash_no_action_are_never_competitors(self):
        alts = (_alt(AlternativeKind.WAIT, None), _alt(AlternativeKind.KEEP_CASH, None), _alt(AlternativeKind.NO_ACTION, None))
        competition = build_capital_competition(_CASE_ID, alts)
        assert competition.competing_alternatives == ()
        assert competition.non_competing_alternatives == alts


class TestBuildPortfolioDecision:
    def test_category_matches_classify_portfolio_decision(self):
        decision = _build(action=DecisionAction.BUY, allocation_rating=FitRating.POOR)
        assert decision.category is PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO

    def test_overweight_fit_rating_becomes_limiting(self):
        decision = _build(allocation_rating=FitRating.POOR)
        codes = [r.reference.id for r in decision.limiting_reasons]
        assert "poor" in codes

    def test_supporting_fit_rating_becomes_supporting(self):
        decision = _build(allocation_rating=FitRating.GOOD)
        codes = [r.reference.id for r in decision.supporting_reasons]
        assert "good" in codes

    def test_competing_alternative_becomes_limiting(self):
        alt = _alt(AlternativeKind.INCREASE_EXISTING_HOLDING)
        decision = _build(action=DecisionAction.BUY, alternatives=(alt,))
        matching = [r for r in decision.limiting_reasons if r.source is PortfolioDecisionReasonSource.OPPORTUNITY_COST]
        assert len(matching) == 1
        assert matching[0].reference.id == "increase_existing_holding"

    def test_large_unallocated_supports_a_buy_decision(self):
        decision = _build(action=DecisionAction.BUY, large_unallocated=True)
        codes = [r.reference.id for r in decision.supporting_reasons]
        assert "large_unallocated" in codes

    def test_large_unallocated_is_irrelevant_to_a_hold_decision(self):
        decision = _build(action=DecisionAction.HOLD, large_unallocated=True)
        codes = [r.reference.id for r in decision.supporting_reasons]
        assert "large_unallocated" not in codes

    def test_high_reliability_becomes_supporting(self):
        decision = _build(reliability_level=ReliabilityLevel.HIGH)
        matching = [r for r in decision.supporting_reasons if r.source is PortfolioDecisionReasonSource.DECISION_RELIABILITY]
        assert len(matching) == 1

    def test_limited_reliability_becomes_limiting(self):
        decision = _build(reliability_level=ReliabilityLevel.LIMITED, allocation_rating=FitRating.NEUTRAL)
        matching = [r for r in decision.limiting_reasons if r.source is PortfolioDecisionReasonSource.DECISION_RELIABILITY]
        assert len(matching) == 1

    def test_every_reference_uses_the_reason_code_kind(self):
        decision = _build(allocation_rating=FitRating.POOR)
        for reason in decision.limiting_reasons:
            assert reason.reference.kind is ExplanationReferenceKind.REASON_CODE

    def test_primary_limiting_reason_is_the_first_entry(self):
        decision = _build(allocation_rating=FitRating.POOR)
        assert decision.primary_limiting_reason == decision.limiting_reasons[0]

    def test_no_limiting_reasons_produces_no_primary(self):
        decision = _build(allocation_rating=FitRating.EXCELLENT)
        assert decision.primary_limiting_reason is None

    def test_watchlist_only_case_falls_back_to_portfolio_wide_concentration(self):
        decision = _build(
            allocation_rating=None,
            is_largest_position=True,
            portfolio_concentration_level=ConcentrationLevel.HIGH,
            action=DecisionAction.BUY,
        )
        assert decision.category is PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO

    def test_two_calls_with_identical_inputs_produce_identical_output(self):
        first = _build(allocation_rating=FitRating.POOR)
        second = _build(allocation_rating=FitRating.POOR)
        assert first == second


class TestSummarize:
    def test_summary_carries_the_same_primary_fact(self):
        decision = _build(allocation_rating=FitRating.POOR)
        summary = summarize_portfolio_decision(decision)
        assert summary.primary_limiting_reason == decision.primary_limiting_reason
        assert summary.category == decision.category


class TestComparePortfolioDecisions:
    def test_never_declares_a_winner_field(self):
        a = _build()
        b = _build()
        comparison = compare_portfolio_decisions(a, b)
        field_names = set(comparison.__dataclass_fields__.keys())
        assert not any("winner" in f or "better_investment" in f for f in field_names)

    def test_better_portfolio_fit_case_id_is_none_on_a_genuine_tie(self):
        a = _build()
        b = _build()
        comparison = compare_portfolio_decisions(a, b)
        assert comparison.better_portfolio_fit_case_id is None

    def test_better_portfolio_fit_case_id_names_the_higher_ranked_side(self):
        a = _build(action=DecisionAction.BUY, allocation_rating=FitRating.POOR)
        b = _build()
        comparison = compare_portfolio_decisions(a, b)
        assert comparison.better_portfolio_fit_case_id == b.case_id

    def test_shared_competitor_case_ids_is_the_real_intersection(self):
        alt = _alt(AlternativeKind.INCREASE_EXISTING_HOLDING, case_id="shared-case")
        a = _build(action=DecisionAction.BUY, alternatives=(alt,))
        b = _build(action=DecisionAction.BUY, alternatives=(alt,))
        comparison = compare_portfolio_decisions(a, b)
        assert comparison.shared_competitor_case_ids == ("shared-case",)


class TestDetectPortfolioDecisionChange:
    def test_first_ever_computation_produces_no_change(self):
        current = _build()
        assert detect_portfolio_decision_change(None, current, detected_at=_NOW) is None

    def test_an_unchanged_decision_produces_no_change(self):
        previous = _build()
        current = _build()
        assert detect_portfolio_decision_change(previous, current, detected_at=_NOW) is None

    def test_category_change_is_detected(self):
        previous = _build(action=DecisionAction.HOLD)
        current = _build(action=DecisionAction.BUY, allocation_rating=FitRating.POOR)
        change = detect_portfolio_decision_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.previous_category is PortfolioDecisionCategory.NEUTRAL
        assert change.current_category is PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO

    def test_new_competitor_is_detected_as_competition_changed(self):
        alt = _alt(AlternativeKind.INCREASE_EXISTING_HOLDING, case_id="new-competitor")
        previous = _build(action=DecisionAction.BUY)
        current = _build(action=DecisionAction.BUY, alternatives=(alt,))
        change = detect_portfolio_decision_change(previous, current, detected_at=_NOW)
        assert change is not None
        assert change.competition_changed is True


class TestPortfolioSynthesisBreakdown:
    def test_supports_portfolio_bucket(self):
        decision = _build(action=DecisionAction.REDUCE, is_largest_position=True, allocation_rating=FitRating.POOR)
        breakdown = build_portfolio_synthesis_breakdown((("AAPL", decision),))
        assert breakdown.supports_portfolio == ("AAPL",)
        assert breakdown.conflicts_with_portfolio == ()

    def test_conflicts_with_portfolio_bucket(self):
        decision = _build(action=DecisionAction.BUY, allocation_rating=FitRating.POOR)
        breakdown = build_portfolio_synthesis_breakdown((("AAPL", decision),))
        assert breakdown.conflicts_with_portfolio == ("AAPL",)
        assert breakdown.supports_portfolio == ()

    def test_highest_capital_competition_bucket(self):
        alt = _alt(AlternativeKind.INCREASE_EXISTING_HOLDING)
        decision = _build(action=DecisionAction.BUY, alternatives=(alt,))
        breakdown = build_portfolio_synthesis_breakdown((("AAPL", decision),))
        assert breakdown.highest_capital_competition == ("AAPL",)

    def test_neutral_bucket(self):
        decision = _build(action=DecisionAction.HOLD)
        breakdown = build_portfolio_synthesis_breakdown((("AAPL", decision),))
        assert breakdown.neutral == ("AAPL",)
