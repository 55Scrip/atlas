"""Tests for `atlas.analysis_engine.direction_selector.select_direction`
(`docs/atlas_decision_engine/DE-008-Direction-Selection.md`,
"Recommendation Backend Step 3").

Pure-function tests only -- no pipeline, no `DecisionEngineInput`, no
fixtures beyond the enum values `select_direction` itself consumes.
Every scenario is named after the `DE-008` matrix row or invariant it
proves."""
from __future__ import annotations

import itertools

import pytest

from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.direction_selector import select_direction
from atlas.analysis_engine.recommendation import RecommendationDirection
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel, HoldingLinkage

EVALUATED = EvaluationState.EVALUATED
NOT_EVALUATED = EvaluationState.NOT_EVALUATED

WEAK = BusinessCategoryStatus.WEAK
MODERATE = BusinessCategoryStatus.MODERATE
STRONG = BusinessCategoryStatus.STRONG
BUSINESS_NOT_EVALUATED = BusinessCategoryStatus.NOT_EVALUATED
BUSINESS_INSUFFICIENT = BusinessCategoryStatus.INSUFFICIENT_INPUT

UNDERVALUED = ValuationStatus.UNDERVALUED
FAIRLY_VALUED = ValuationStatus.FAIRLY_VALUED
EXPENSIVE = ValuationStatus.EXPENSIVE
VALUATION_NOT_EVALUATED = ValuationStatus.NOT_EVALUATED
VALUATION_INSUFFICIENT = ValuationStatus.INSUFFICIENT_INPUT

ABSENT = HoldingLinkage.ABSENT
PRESENT = HoldingLinkage.PRESENT


def _select(**overrides) -> RecommendationDirection | None:
    """Every keyword defaults to a "clear hard gate, strong business,
    unheld, no dampening, no contradicting evidence" baseline -- each
    test overrides only the dimension(s) it means to exercise, so a
    failure points at exactly one changed input."""
    fields = dict(
        holding_linkage=ABSENT,
        business_evaluation_state=EVALUATED,
        valuation_state=EVALUATED,
        portfolio_intelligence_state=EVALUATED,
        reasoning_state=EVALUATED,
        evidence_coverage=EvidenceCoverageLevel.FULL,
        growth_status=STRONG,
        capital_allocation_status=STRONG,
        valuation_status=FAIRLY_VALUED,
        has_portfolio_dampening=False,
        has_high_financial_or_valuation_risk=False,
    )
    fields.update(overrides)
    return select_direction(**fields)


# ---------------------------------------------------------------------------
# Hard gate (DE-008 §4, §18 stage 1)
# ---------------------------------------------------------------------------


class TestHardGate:
    @pytest.mark.parametrize(
        "field",
        [
            "business_evaluation_state",
            "valuation_state",
            "portfolio_intelligence_state",
            "reasoning_state",
        ],
    )
    def test_any_unevaluated_stage_withholds(self, field):
        assert _select(**{field: NOT_EVALUATED}) is None

    @pytest.mark.parametrize(
        "coverage", [EvidenceCoverageLevel.NOT_APPLICABLE, EvidenceCoverageLevel.NONE]
    )
    def test_no_evidence_coverage_withholds(self, coverage):
        assert _select(evidence_coverage=coverage) is None

    def test_hard_gate_checked_before_any_positive_case_reasoning(self):
        """A failed hard gate withholds even for a held position with
        otherwise strong, favorable inputs -- nothing downstream can
        override RecommendationWithheld."""
        assert (
            _select(
                holding_linkage=PRESENT,
                growth_status=STRONG,
                valuation_status=FAIRLY_VALUED,
                business_evaluation_state=NOT_EVALUATED,
            )
            is None
        )


# ---------------------------------------------------------------------------
# EXIT unreachability (DE-008 §9's own criterion is real, but the only
# candidate signal this codebase computes today -- ordinary Counter-
# Evidence -- is not doctrinally sufficient to satisfy it; see
# direction_selector.py's own "On EXIT" for the full reasoning. An
# earlier version of this file tested "any contradicting evidence ->
# EXIT," which was itself the semantic error, found during pre-commit
# review: DE-004 §3 defines that identical fact as compatible with a
# continuing direction at Medium conviction, not as grounds for a forced
# exit.)
# ---------------------------------------------------------------------------


class TestExitUnreachable:
    def test_select_direction_accepts_no_contradicting_evidence_parameter(self):
        """`select_direction` has no `has_contradicting_evidence`
        parameter at all -- Counter-Evidence cannot influence Direction
        Selection in any way, not even indirectly."""
        import inspect

        parameters = inspect.signature(select_direction).parameters
        assert "has_contradicting_evidence" not in parameters

    def test_expensive_valuation_alone_on_held_position_is_trim_not_exit(self):
        """DE-008 §21 invariant 6: EXIT SHALL NOT be produced from
        Valuation Evidence alone, however extreme."""
        assert _select(holding_linkage=PRESENT, valuation_status=EXPENSIVE) is RecommendationDirection.TRIM

    def test_dampening_alone_on_held_position_is_not_exit(self):
        """Portfolio/Risk dampening never composes into EXIT (DE-008
        §12, §13, §21 invariant 9)."""
        result = _select(
            holding_linkage=PRESENT,
            has_portfolio_dampening=True,
            has_high_financial_or_valuation_risk=True,
        )
        assert result is not RecommendationDirection.EXIT

    def test_weak_business_on_held_position_is_trim_not_exit(self):
        assert _select(holding_linkage=PRESENT, growth_status=WEAK) is not RecommendationDirection.EXIT


# ---------------------------------------------------------------------------
# Weak business (DE-008 §10.2, §20) -- independently sufficient
# ---------------------------------------------------------------------------


class TestWeakBusiness:
    def test_weak_growth_not_held_is_no_action(self):
        assert _select(holding_linkage=ABSENT, growth_status=WEAK) is RecommendationDirection.NO_ACTION

    def test_weak_capital_allocation_not_held_is_no_action(self):
        assert (
            _select(holding_linkage=ABSENT, capital_allocation_status=WEAK) is RecommendationDirection.NO_ACTION
        )

    def test_weak_business_held_is_trim(self):
        assert _select(holding_linkage=PRESENT, growth_status=WEAK) is RecommendationDirection.TRIM

    def test_weak_business_overrides_undervalued(self):
        """Business and Valuation are independent (DE-008 §10.2) --
        positive Valuation Evidence cannot rescue a WEAK Business
        conclusion."""
        assert (
            _select(holding_linkage=ABSENT, growth_status=WEAK, valuation_status=UNDERVALUED)
            is RecommendationDirection.NO_ACTION
        )

    def test_weak_business_independent_of_dampening(self):
        assert (
            _select(holding_linkage=PRESENT, growth_status=WEAK, has_portfolio_dampening=False)
            is RecommendationDirection.TRIM
        )


# ---------------------------------------------------------------------------
# Business status unknown (implementation-level gap DE-008 doesn't
# enumerate -- see direction_selector.py's own docstring)
# ---------------------------------------------------------------------------


class TestBusinessInconclusive:
    def test_both_categories_inconclusive_withholds_not_held(self):
        assert (
            _select(
                holding_linkage=ABSENT,
                growth_status=BUSINESS_INSUFFICIENT,
                capital_allocation_status=BUSINESS_NOT_EVALUATED,
            )
            is None
        )

    def test_both_categories_inconclusive_withholds_held(self):
        assert (
            _select(
                holding_linkage=PRESENT,
                growth_status=BUSINESS_NOT_EVALUATED,
                capital_allocation_status=BUSINESS_INSUFFICIENT,
            )
            is None
        )

    def test_one_conclusive_category_is_enough_to_be_positive(self):
        """Growth STRONG, Capital Allocation inconclusive -> still
        `POSITIVE` (DE-008's matrix never distinguishes MODERATE from
        STRONG, and one real conclusion is enough to leave INSUFFICIENT)."""
        result = _select(
            holding_linkage=PRESENT,
            growth_status=STRONG,
            capital_allocation_status=BUSINESS_INSUFFICIENT,
            valuation_status=FAIRLY_VALUED,
        )
        assert result is RecommendationDirection.HOLD


# ---------------------------------------------------------------------------
# The two required RecommendationWithheld scenarios (task-specified)
# ---------------------------------------------------------------------------


class TestValuationSupportForCapitalDeploymentGap:
    def test_undervalued_good_business_no_dampening_not_held_is_withheld(self):
        """Not held + strong business + UNDERVALUED + no dampening ->
        RecommendationWithheld, never BUY."""
        result = _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED)
        assert result is None

    def test_undervalued_good_business_no_dampening_held_is_withheld(self):
        """Held + strong business + UNDERVALUED + no dampening ->
        RecommendationWithheld, never ADD, and never a HOLD fallback
        (UNDERVALUED is HOLD's own favorable extreme -- DE-008 §20)."""
        result = _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED)
        assert result is None

    def test_undervalued_not_held_with_dampening_is_no_action(self):
        """Dampening is real, independent evidence -- it rescues this
        cell from RecommendationWithheld into a genuine NO_ACTION (DE-008
        §20's not-held table)."""
        result = _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED, has_portfolio_dampening=True)
        assert result is RecommendationDirection.NO_ACTION

    def test_undervalued_held_with_dampening_is_trim(self):
        result = _select(
            holding_linkage=PRESENT, valuation_status=UNDERVALUED, has_high_financial_or_valuation_risk=True
        )
        assert result is RecommendationDirection.TRIM

    def test_fairly_valued_not_held_no_dampening_is_also_withheld(self):
        """FAIRLY_VALUED is treated identically to UNDERVALUED here --
        neither constitutes Valuation Support for Capital Deployment
        (DE-008 §20's own note on this)."""
        result = _select(holding_linkage=ABSENT, valuation_status=FAIRLY_VALUED)
        assert result is None

    def test_valuation_inconclusive_positive_business_withholds(self):
        """No real Valuation Evidence at all (not even the
        historically-relative signal) -- withheld, not guessed."""
        assert _select(holding_linkage=ABSENT, valuation_status=VALUATION_NOT_EVALUATED) is None
        assert _select(holding_linkage=PRESENT, valuation_status=VALUATION_INSUFFICIENT) is None


# ---------------------------------------------------------------------------
# EXPENSIVE -> TRIM (held) / NO_ACTION (not held)
# ---------------------------------------------------------------------------


class TestExpensiveValuation:
    def test_expensive_held_is_trim(self):
        assert _select(holding_linkage=PRESENT, valuation_status=EXPENSIVE) is RecommendationDirection.TRIM

    def test_expensive_held_is_trim_regardless_of_dampening(self):
        assert (
            _select(holding_linkage=PRESENT, valuation_status=EXPENSIVE, has_portfolio_dampening=True)
            is RecommendationDirection.TRIM
        )

    def test_expensive_not_held_is_no_action(self):
        assert _select(holding_linkage=ABSENT, valuation_status=EXPENSIVE) is RecommendationDirection.NO_ACTION


# ---------------------------------------------------------------------------
# FAIRLY_VALUED + intact thesis -> HOLD
# ---------------------------------------------------------------------------


class TestHold:
    def test_fairly_valued_held_no_dampening_is_hold(self):
        assert (
            _select(holding_linkage=PRESENT, valuation_status=FAIRLY_VALUED) is RecommendationDirection.HOLD
        )

    def test_fairly_valued_held_with_dampening_is_trim_not_hold(self):
        assert (
            _select(holding_linkage=PRESENT, valuation_status=FAIRLY_VALUED, has_portfolio_dampening=True)
            is RecommendationDirection.TRIM
        )

    def test_hold_requires_a_holding(self):
        """HOLD is structurally unreachable for an unheld security (DE-008
        §3's position-state partition)."""
        result = _select(holding_linkage=ABSENT, valuation_status=FAIRLY_VALUED)
        assert result is not RecommendationDirection.HOLD


# ---------------------------------------------------------------------------
# NO_ACTION genuine vs. disguised (DE-008 §19's governing test)
# ---------------------------------------------------------------------------


class TestNoAction:
    def test_no_action_requires_no_holding(self):
        result = _select(holding_linkage=ABSENT, valuation_status=EXPENSIVE)
        assert result is RecommendationDirection.NO_ACTION

    def test_no_action_never_produced_for_held_position(self):
        """NO_ACTION is structurally unreachable once held (DE-008 §3)."""
        for valuation in (UNDERVALUED, FAIRLY_VALUED, EXPENSIVE):
            result = _select(holding_linkage=PRESENT, valuation_status=valuation, has_portfolio_dampening=True)
            assert result is not RecommendationDirection.NO_ACTION


# ---------------------------------------------------------------------------
# BUY / ADD structural unreachability
# ---------------------------------------------------------------------------


class TestBuyAddUnreachable:
    def test_buy_never_returned_for_the_most_favorable_case(self):
        """The single most BUY-favorable input this function accepts --
        unheld, strong business both categories, UNDERVALUED, no
        dampening -- still SHALL NOT return BUY (DE-008 §21 invariant 1)."""
        result = _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED)
        assert result is not RecommendationDirection.BUY
        assert result is None

    def test_add_never_returned_for_the_most_favorable_case(self):
        result = _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED)
        assert result is not RecommendationDirection.ADD
        assert result is None

    def test_exhaustive_sweep_never_produces_buy_add_or_exit(self):
        """Exhaustive over every categorical/boolean input this function
        accepts (with the hard gate held open, since a closed gate
        trivially returns None) -- BUY, ADD, and EXIT SHALL NOT appear in
        the output for any combination, not merely the ones spot-checked
        above."""
        business_statuses = (
            BUSINESS_NOT_EVALUATED,
            BUSINESS_INSUFFICIENT,
            WEAK,
            MODERATE,
            STRONG,
        )
        valuation_statuses = (
            VALUATION_NOT_EVALUATED,
            VALUATION_INSUFFICIENT,
            UNDERVALUED,
            FAIRLY_VALUED,
            EXPENSIVE,
        )
        seen_directions = set()
        for (
            holding_linkage,
            growth_status,
            capital_allocation_status,
            valuation_status,
            has_portfolio_dampening,
            has_high_financial_or_valuation_risk,
        ) in itertools.product(
            (ABSENT, PRESENT),
            business_statuses,
            business_statuses,
            valuation_statuses,
            (False, True),
            (False, True),
        ):
            result = select_direction(
                holding_linkage=holding_linkage,
                business_evaluation_state=EVALUATED,
                valuation_state=EVALUATED,
                portfolio_intelligence_state=EVALUATED,
                reasoning_state=EVALUATED,
                evidence_coverage=EvidenceCoverageLevel.FULL,
                growth_status=growth_status,
                capital_allocation_status=capital_allocation_status,
                valuation_status=valuation_status,
                has_portfolio_dampening=has_portfolio_dampening,
                has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
            )
            assert result is not RecommendationDirection.BUY
            assert result is not RecommendationDirection.ADD
            assert result is not RecommendationDirection.EXIT
            seen_directions.add(result)

        # Every other reachable outcome SHALL appear at least once across
        # the sweep -- confirms the sweep is actually exercising the full
        # decision procedure, not vacuously passing.
        assert seen_directions == {
            None,
            RecommendationDirection.HOLD,
            RecommendationDirection.TRIM,
            RecommendationDirection.NO_ACTION,
        }


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterministic:
    def test_identical_inputs_produce_identical_results(self):
        kwargs = dict(
            holding_linkage=PRESENT,
            business_evaluation_state=EVALUATED,
            valuation_state=EVALUATED,
            portfolio_intelligence_state=EVALUATED,
            reasoning_state=EVALUATED,
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=STRONG,
            capital_allocation_status=MODERATE,
            valuation_status=EXPENSIVE,
            has_portfolio_dampening=False,
            has_high_financial_or_valuation_risk=True,
        )
        assert select_direction(**kwargs) == select_direction(**kwargs) == RecommendationDirection.TRIM
