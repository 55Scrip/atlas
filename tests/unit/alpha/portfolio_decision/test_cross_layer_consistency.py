"""Cross-layer consistency property tests for Portfolio Decision
Synthesis (Deliverable 12). Exhaustive over the closed vocabularies
involved -- the same discipline `tests/unit/alpha/decision_reliability
/test_cross_layer_consistency.py` already established."""
from __future__ import annotations

from itertools import product

import pytest

from atlas.alpha.decision_reliability.models import ReliabilityLevel
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.portfolio_decision.engine import classify_portfolio_decision
from atlas.alpha.portfolio_decision.models import PortfolioDecisionCategory

_CATEGORY_ORDER = [
    PortfolioDecisionCategory.UNKNOWN,
    PortfolioDecisionCategory.OPERATIONALLY_LIMITED,
    PortfolioDecisionCategory.CONFLICTS_WITH_PORTFOLIO,
    PortfolioDecisionCategory.REQUIRES_REVIEW,
    PortfolioDecisionCategory.NEUTRAL,
    PortfolioDecisionCategory.SUPPORTS_PORTFOLIO,
]


class TestClassificationIsDeterministic:
    """Exhaustive over every (action, reliability, overweight,
    competition) combination this codebase's own closed vocabularies
    allow -- identical inputs must always produce the identical
    category, and the result must always be a real
    `PortfolioDecisionCategory` member."""

    @pytest.mark.parametrize(
        "action,reliability,overweight,competition",
        list(product(DecisionAction, ReliabilityLevel, (True, False), (True, False))),
    )
    def test_classification_is_pure_and_always_a_real_category(self, action, reliability, overweight, competition):
        first = classify_portfolio_decision(action, reliability, overweight, competition)
        second = classify_portfolio_decision(action, reliability, overweight, competition)
        assert first == second
        assert first in _CATEGORY_ORDER


class TestClassificationNeverContradictsReliabilityFloorStates:
    """`UNKNOWN`/`UNAVAILABLE` reliability are floor states no
    portfolio context can override -- exhaustive check that this holds
    for every real action/overweight/competition combination."""

    @pytest.mark.parametrize("action,overweight,competition", list(product(DecisionAction, (True, False), (True, False))))
    def test_unknown_reliability_always_yields_unknown_category(self, action, overweight, competition):
        assert classify_portfolio_decision(action, ReliabilityLevel.UNKNOWN, overweight, competition) is PortfolioDecisionCategory.UNKNOWN

    @pytest.mark.parametrize("action,overweight,competition", list(product(DecisionAction, (True, False), (True, False))))
    def test_unavailable_reliability_always_yields_operationally_limited(self, action, overweight, competition):
        assert (
            classify_portfolio_decision(action, ReliabilityLevel.UNAVAILABLE, overweight, competition)
            is PortfolioDecisionCategory.OPERATIONALLY_LIMITED
        )


class TestCapitalIncreasingAndDecreasingActionsNeverAgreeOnAnOverweightHolding:
    """A capital-increasing action on an overweight holding must never
    classify the same as a capital-decreasing action on the same
    overweight holding -- they are opposite portfolio facts and must
    never collapse to the same category."""

    @pytest.mark.parametrize("reliability", [ReliabilityLevel.HIGH, ReliabilityLevel.MODERATE, ReliabilityLevel.LIMITED])
    def test_buy_and_reduce_diverge_on_an_overweight_holding(self, reliability):
        increasing = classify_portfolio_decision(DecisionAction.BUY, reliability, True, False)
        decreasing = classify_portfolio_decision(DecisionAction.REDUCE, reliability, True, False)
        assert increasing != decreasing
