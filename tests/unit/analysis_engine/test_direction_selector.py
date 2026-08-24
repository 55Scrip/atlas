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
from atlas.analysis_engine.valuation.support import ValuationSupportStatus
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

SUPPORTED = ValuationSupportStatus.SUPPORTED
NOT_SUPPORTED = ValuationSupportStatus.NOT_SUPPORTED
VALUATION_SUPPORT_INSUFFICIENT = ValuationSupportStatus.INSUFFICIENT_INPUT


def _select(**overrides) -> RecommendationDirection | None:
    """Every keyword defaults to a "clear hard gate, strong business,
    unheld, no dampening, no contradicting evidence, Valuation Support
    for Capital Deployment not established" baseline -- each test
    overrides only the dimension(s) it means to exercise, so a failure
    points at exactly one changed input. `valuation_support_status`
    defaults to `INSUFFICIENT_INPUT` -- the permanent, universal state
    every real company was in before `DE-015` was implemented -- so every
    pre-`DE-016` test in this file keeps its exact prior meaning
    unchanged unless it explicitly opts into `SUPPORTED`."""
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
        valuation_support_status=VALUATION_SUPPORT_INSUFFICIENT,
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
    def test_no_evidence_from_either_source_withholds(self, coverage):
        """Recommendation Evidence Sufficiency Alignment: withholding
        now requires *both* evidence sources to be absent -- no
        Observation-linked Evidence coverage AND no real company-
        fundamentals conclusion (Growth/Capital Allocation/Valuation/
        Risk all inconclusive)."""
        assert (
            _select(
                evidence_coverage=coverage,
                growth_status=BUSINESS_NOT_EVALUATED,
                capital_allocation_status=BUSINESS_INSUFFICIENT,
                valuation_status=VALUATION_INSUFFICIENT,
                has_real_risk_evidence=False,
            )
            is None
        )

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
# Recommendation Evidence Sufficiency Alignment: Stage 1's evidence-
# existence check now recognizes two independent evidence sources --
# Core-Domain Observation/Evidence coverage (`evidence_coverage`,
# pre-existing) and provenance-backed company-fundamentals evidence
# (`growth_status`/`capital_allocation_status`/`valuation_status`,
# already this function's own parameters, plus the new
# `has_real_risk_evidence`) -- either one alone is now sufficient to
# reach the real matrix. Governing principle: Atlas-generated,
# provenance-backed company analysis is real evidence; a Core-Domain
# Observation may strengthen it but is not mandatory for it.
# ---------------------------------------------------------------------------


class TestRecommendationEvidenceSufficiencyAlignment:
    def test_no_observation_but_real_growth_evidence_reaches_the_matrix(self):
        """No Observation-linked Evidence at all (`NOT_APPLICABLE`), but
        a real, provenance-backed Growth conclusion plus a real,
        conclusive Valuation status -- reaches the real matrix and
        resolves to a real direction, not RecommendationWithheld. (A
        real Business conclusion alone, with Valuation still
        inconclusive, correctly stays withheld -- `DE-008`'s own "needs
        to know which ValuationStatus applies" gap, untouched here; see
        `test_no_observation_but_real_valuation_evidence_reaches_the_matrix`
        for that half of the evidence-source proof.)"""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.NOT_APPLICABLE,
            growth_status=STRONG,
            capital_allocation_status=BUSINESS_INSUFFICIENT,
            valuation_status=FAIRLY_VALUED,
            has_real_risk_evidence=False,
            holding_linkage=PRESENT,
        )
        assert result is RecommendationDirection.HOLD

    def test_no_observation_but_real_valuation_evidence_reaches_the_matrix(self):
        """Growth/Capital Allocation both inconclusive, but a real FCF
        valuation conclusion alone is enough evidence to pass Stage 1 --
        the matrix itself still withholds here (business INSUFFICIENT,
        untouched by this change) -- proving Stage 1 passing does not
        force a fabricated direction."""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.NONE,
            growth_status=BUSINESS_INSUFFICIENT,
            capital_allocation_status=BUSINESS_NOT_EVALUATED,
            valuation_status=FAIRLY_VALUED,
            has_real_risk_evidence=False,
        )
        assert result is None

    def test_no_observation_and_no_real_company_evidence_stays_withheld(self):
        """Neither evidence source present -- still RecommendationWithheld,
        unchanged from before this alignment."""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.NOT_APPLICABLE,
            growth_status=BUSINESS_NOT_EVALUATED,
            capital_allocation_status=BUSINESS_INSUFFICIENT,
            valuation_status=VALUATION_NOT_EVALUATED,
            has_real_risk_evidence=False,
        )
        assert result is None

    def test_observation_backed_case_is_unaffected(self):
        """`evidence_coverage=FULL` (the old, sole evidence source)
        behaves exactly as before this alignment, regardless of company-
        fundamentals evidence -- confirms the fix is additive, not a
        replacement."""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=STRONG,
            capital_allocation_status=STRONG,
            valuation_status=FAIRLY_VALUED,
            has_real_risk_evidence=False,
            holding_linkage=PRESENT,
        )
        assert result is RecommendationDirection.HOLD

    def test_weak_company_evidence_counts_as_evidence_not_absence(self):
        """A real but negative Growth conclusion (`WEAK`) is still real,
        provenance-backed evidence -- passes Stage 1 and resolves via
        the matrix's own WEAK-business branch (TRIM/NO_ACTION), never
        treated as if no evidence existed."""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.NOT_APPLICABLE,
            growth_status=WEAK,
            capital_allocation_status=BUSINESS_INSUFFICIENT,
            valuation_status=VALUATION_INSUFFICIENT,
            has_real_risk_evidence=False,
            holding_linkage=ABSENT,
        )
        assert result is RecommendationDirection.NO_ACTION

    def test_insufficient_input_does_not_count_as_evidence(self):
        """`INSUFFICIENT_INPUT` (Growth/Capital Allocation/Valuation) and
        `NOT_EVALUATED` are both still treated as "no conclusion" -- only
        a real categorical status counts."""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.NONE,
            growth_status=BUSINESS_INSUFFICIENT,
            capital_allocation_status=BUSINESS_INSUFFICIENT,
            valuation_status=VALUATION_INSUFFICIENT,
            has_real_risk_evidence=False,
        )
        assert result is None

    def test_real_risk_evidence_alone_passes_stage_one_but_matrix_still_withholds_without_business(self):
        """`has_real_risk_evidence=True` alone is enough real evidence to
        pass Stage 1 -- but the matrix's own untouched
        business-INSUFFICIENT branch still withholds when Growth/Capital
        Allocation/Valuation are all inconclusive. Proves risk evidence
        passing Stage 1 never forces a fabricated direction."""
        result = _select(
            evidence_coverage=EvidenceCoverageLevel.NOT_APPLICABLE,
            growth_status=BUSINESS_NOT_EVALUATED,
            capital_allocation_status=BUSINESS_INSUFFICIENT,
            valuation_status=VALUATION_INSUFFICIENT,
            has_real_risk_evidence=True,
        )
        assert result is None

    def test_has_real_risk_evidence_defaults_false(self):
        """Every existing call site that never supplies this new
        parameter keeps its exact prior behavior."""
        import inspect

        assert inspect.signature(select_direction).parameters["has_real_risk_evidence"].default is False


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
# The Valuation Support for Capital Deployment gap (DE-016: this gap is
# now closeable -- these tests exercise the still-unmet cases, using
# `_select`'s own INSUFFICIENT_INPUT default; `TestBuyAddReachability`
# below exercises the now-real SUPPORTED case.)
# ---------------------------------------------------------------------------


class TestValuationSupportForCapitalDeploymentGap:
    def test_undervalued_good_business_no_dampening_not_held_is_withheld(self):
        """Not held + strong business + UNDERVALUED + no dampening,
        Valuation Support not established -> RecommendationWithheld,
        never BUY."""
        result = _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED)
        assert result is None

    def test_undervalued_good_business_no_dampening_held_is_withheld(self):
        """Held + strong business + UNDERVALUED + no dampening,
        Valuation Support not established -> RecommendationWithheld,
        never ADD, and never a HOLD fallback (UNDERVALUED is HOLD's own
        favorable extreme -- DE-008 §20)."""
        result = _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED)
        assert result is None

    def test_undervalued_not_held_with_dampening_is_no_action(self):
        """Dampening is real, independent evidence -- it rescues this
        cell from RecommendationWithheld into a genuine NO_ACTION (DE-008
        §20's not-held table), regardless of Valuation Support."""
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

    def test_not_supported_behaves_identically_to_insufficient_input_not_held(self):
        """DE-016 Phase 6/13: `NOT_SUPPORTED` and `INSUFFICIENT_INPUT`
        both mean "the prerequisite is not established" -- neither
        acquires new semantics."""
        for status in (NOT_SUPPORTED, VALUATION_SUPPORT_INSUFFICIENT):
            for valuation_status in (UNDERVALUED, FAIRLY_VALUED):
                assert _select(
                    holding_linkage=ABSENT, valuation_status=valuation_status, valuation_support_status=status
                ) is None

    def test_not_supported_behaves_identically_to_insufficient_input_held(self):
        for status in (NOT_SUPPORTED, VALUATION_SUPPORT_INSUFFICIENT):
            assert _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED, valuation_support_status=status) is None

    def test_not_supported_never_becomes_trim_where_insufficient_input_would_not(self):
        """DE-016 Phase 13's own required negative-semantics proof:
        NOT_SUPPORTED must not independently produce TRIM where the
        identical INSUFFICIENT_INPUT case would not."""
        held_fairly_valued_no_dampening = dict(holding_linkage=PRESENT, valuation_status=FAIRLY_VALUED)
        result_not_supported = _select(**held_fairly_valued_no_dampening, valuation_support_status=NOT_SUPPORTED)
        result_insufficient = _select(**held_fairly_valued_no_dampening, valuation_support_status=VALUATION_SUPPORT_INSUFFICIENT)
        assert result_not_supported is RecommendationDirection.HOLD
        assert result_not_supported is result_insufficient

    def test_not_supported_never_produces_exit(self):
        assert _select(holding_linkage=PRESENT, valuation_status=EXPENSIVE, valuation_support_status=NOT_SUPPORTED) is not RecommendationDirection.EXIT

    def test_supported_never_weakens_weak_business_independently_sufficient_trim(self):
        """DE-016 Phase 13: SUPPORTED must not weaken any existing
        TRIM/HOLD/NO_ACTION rule that is independently sufficient --
        WEAK Business still wins regardless."""
        assert (
            _select(holding_linkage=PRESENT, growth_status=WEAK, valuation_support_status=SUPPORTED)
            is RecommendationDirection.TRIM
        )
        assert (
            _select(holding_linkage=ABSENT, growth_status=WEAK, valuation_support_status=SUPPORTED)
            is RecommendationDirection.NO_ACTION
        )

    def test_supported_never_changes_fairly_valued_held_hold_into_add(self):
        """FAIRLY_VALUED + held + no dampening was never one of the cells
        DE-008 §20 blocks on this prerequisite -- it already resolves via
        HOLD's own independent criterion (DE-008 §10.2) and stays HOLD
        even when Valuation Support is SUPPORTED, per DE-016's own
        "only touch the currently-blocked cells" scope."""
        assert (
            _select(holding_linkage=PRESENT, valuation_status=FAIRLY_VALUED, valuation_support_status=SUPPORTED)
            is RecommendationDirection.HOLD
        )

    def test_supported_never_changes_expensive_into_buy_or_add(self):
        assert (
            _select(holding_linkage=ABSENT, valuation_status=EXPENSIVE, valuation_support_status=SUPPORTED)
            is RecommendationDirection.NO_ACTION
        )
        assert (
            _select(holding_linkage=PRESENT, valuation_status=EXPENSIVE, valuation_support_status=SUPPORTED)
            is RecommendationDirection.TRIM
        )


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
# EXIT: still unreachable regardless of Valuation Support (DE-016 Phase 14
# invariant 6)
# ---------------------------------------------------------------------------

_BUSINESS_STATUSES = (BUSINESS_NOT_EVALUATED, BUSINESS_INSUFFICIENT, WEAK, MODERATE, STRONG)
_VALUATION_STATUSES = (VALUATION_NOT_EVALUATED, VALUATION_INSUFFICIENT, UNDERVALUED, FAIRLY_VALUED, EXPENSIVE)
_VALUATION_SUPPORT_STATUSES = (SUPPORTED, NOT_SUPPORTED, VALUATION_SUPPORT_INSUFFICIENT)


def _full_sweep(valuation_support_status: ValuationSupportStatus) -> dict[tuple, RecommendationDirection | None]:
    """Every categorical/boolean input this function accepts, at one
    fixed `valuation_support_status`, with the hard gate held open (a
    closed gate trivially returns `None`) -- keyed by the exact input
    tuple so two sweeps can be compared cell by cell."""
    results: dict[tuple, RecommendationDirection | None] = {}
    for (
        holding_linkage,
        growth_status,
        capital_allocation_status,
        valuation_status,
        has_portfolio_dampening,
        has_high_financial_or_valuation_risk,
    ) in itertools.product(
        (ABSENT, PRESENT),
        _BUSINESS_STATUSES,
        _BUSINESS_STATUSES,
        _VALUATION_STATUSES,
        (False, True),
        (False, True),
    ):
        key = (
            holding_linkage,
            growth_status,
            capital_allocation_status,
            valuation_status,
            has_portfolio_dampening,
            has_high_financial_or_valuation_risk,
        )
        results[key] = select_direction(
            holding_linkage=holding_linkage,
            business_evaluation_state=EVALUATED,
            valuation_state=EVALUATED,
            portfolio_intelligence_state=EVALUATED,
            reasoning_state=EVALUATED,
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=growth_status,
            capital_allocation_status=capital_allocation_status,
            valuation_status=valuation_status,
            valuation_support_status=valuation_support_status,
            has_portfolio_dampening=has_portfolio_dampening,
            has_high_financial_or_valuation_risk=has_high_financial_or_valuation_risk,
        )
    return results


class TestExitNeverReachable:
    def test_exhaustive_sweep_never_produces_exit_at_any_valuation_support_status(self):
        """DE-008 §21 invariant 6, re-verified after DE-016: no
        combination of inputs, at any `ValuationSupportStatus`, ever
        produces EXIT."""
        for valuation_support_status in _VALUATION_SUPPORT_STATUSES:
            sweep = _full_sweep(valuation_support_status)
            assert RecommendationDirection.EXIT not in sweep.values()


# ---------------------------------------------------------------------------
# BUY / ADD reachability (DE-016)
# ---------------------------------------------------------------------------


class TestBuyAddReachability:
    def test_buy_reachable_for_the_most_favorable_case(self):
        """The single most BUY-favorable input this function accepts --
        unheld, strong business both categories, UNDERVALUED, no
        dampening -- now returns BUY once Valuation Support for Capital
        Deployment is SUPPORTED (DE-008 §21 invariant 1, satisfied)."""
        result = _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED)
        assert result is RecommendationDirection.BUY

    def test_add_reachable_for_the_most_favorable_case(self):
        result = _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED)
        assert result is RecommendationDirection.ADD

    def test_buy_reachable_from_fairly_valued_too(self):
        """DE-008 §20's own note: UNDERVALUED and FAIRLY_VALUED are
        treated identically for the not-held, capital-deployment-gated
        cells."""
        result = _select(holding_linkage=ABSENT, valuation_status=FAIRLY_VALUED, valuation_support_status=SUPPORTED)
        assert result is RecommendationDirection.BUY

    def test_buy_still_none_when_not_supported(self):
        result = _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED, valuation_support_status=NOT_SUPPORTED)
        assert result is None

    def test_buy_still_none_when_insufficient_input(self):
        result = _select(
            holding_linkage=ABSENT, valuation_status=UNDERVALUED, valuation_support_status=VALUATION_SUPPORT_INSUFFICIENT
        )
        assert result is None

    def test_add_still_none_when_not_supported(self):
        result = _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED, valuation_support_status=NOT_SUPPORTED)
        assert result is None

    def test_business_weak_blocks_buy_even_when_supported(self):
        assert (
            _select(holding_linkage=ABSENT, growth_status=WEAK, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED)
            is RecommendationDirection.NO_ACTION
        )

    def test_dampening_blocks_buy_even_when_supported(self):
        """DE-008 §12: Portfolio/Risk dampening never manufactures a
        positive direction -- SUPPORTED does not override it."""
        result = _select(
            holding_linkage=ABSENT,
            valuation_status=UNDERVALUED,
            valuation_support_status=SUPPORTED,
            has_portfolio_dampening=True,
        )
        assert result is RecommendationDirection.NO_ACTION
        assert result is not RecommendationDirection.BUY

    def test_dampening_blocks_add_even_when_supported(self):
        result = _select(
            holding_linkage=PRESENT,
            valuation_status=UNDERVALUED,
            valuation_support_status=SUPPORTED,
            has_high_financial_or_valuation_risk=True,
        )
        assert result is RecommendationDirection.TRIM
        assert result is not RecommendationDirection.ADD

    def test_hard_gate_blocks_buy_even_when_supported(self):
        result = _select(
            holding_linkage=ABSENT,
            valuation_status=UNDERVALUED,
            valuation_support_status=SUPPORTED,
            business_evaluation_state=NOT_EVALUATED,
        )
        assert result is None

    def test_expensive_never_produces_buy_or_add_even_when_supported(self):
        """DE-016: not inventing a new BUY/ADD path outside the
        already-adopted matrix -- EXPENSIVE stays TRIM/NO_ACTION."""
        assert (
            _select(holding_linkage=ABSENT, valuation_status=EXPENSIVE, valuation_support_status=SUPPORTED)
            is RecommendationDirection.NO_ACTION
        )
        assert (
            _select(holding_linkage=PRESENT, valuation_status=EXPENSIVE, valuation_support_status=SUPPORTED)
            is RecommendationDirection.TRIM
        )

    def test_exhaustive_sweep_at_not_supported_never_produces_buy_add_or_exit(self):
        """Exact re-verification of the module's pre-DE-016 guarantee,
        now parameterized by the new input: with the prerequisite
        unestablished, the reachable-outcome set is unchanged."""
        sweep = _full_sweep(NOT_SUPPORTED)
        seen = set(sweep.values())
        assert RecommendationDirection.BUY not in seen
        assert RecommendationDirection.ADD not in seen
        assert RecommendationDirection.EXIT not in seen
        assert seen == {None, RecommendationDirection.HOLD, RecommendationDirection.TRIM, RecommendationDirection.NO_ACTION}

    def test_exhaustive_sweep_at_insufficient_input_is_identical_to_not_supported(self):
        """DE-016 Phase 6's own required regression: NOT_SUPPORTED and
        INSUFFICIENT_INPUT produce identical Direction behavior across
        every other input, held constant."""
        assert _full_sweep(NOT_SUPPORTED) == _full_sweep(VALUATION_SUPPORT_INSUFFICIENT)

    def test_exhaustive_sweep_at_supported_differs_from_not_supported_only_at_the_two_reserved_cells(self):
        """The strongest available proof of minimality: comparing the
        full sweep cell by cell, `SUPPORTED` changes the outcome only at
        exactly the cells `DE-008` §20 marks as blocked purely by this
        prerequisite (not-held: UNDERVALUED/FAIRLY_VALUED, no dampening;
        held: UNDERVALUED, no dampening) -- and only from `None` to
        `BUY`/`ADD`, never anything else, anywhere else."""
        not_supported = _full_sweep(NOT_SUPPORTED)
        supported = _full_sweep(SUPPORTED)
        assert set(not_supported.keys()) == set(supported.keys())

        changed_cells = {key: (not_supported[key], supported[key]) for key in not_supported if not_supported[key] != supported[key]}

        for key, (before, after) in changed_cells.items():
            (
                holding_linkage,
                growth_status,
                capital_allocation_status,
                valuation_status,
                has_portfolio_dampening,
                has_high_financial_or_valuation_risk,
            ) = key
            dampening = has_portfolio_dampening or has_high_financial_or_valuation_risk
            assert before is None, f"expected a currently-blocked cell, found {before!r} at {key}"
            assert not dampening
            assert valuation_status in (UNDERVALUED, FAIRLY_VALUED)
            business_positive = growth_status in (MODERATE, STRONG) or capital_allocation_status in (MODERATE, STRONG)
            business_weak = growth_status is WEAK or capital_allocation_status is WEAK
            assert business_positive and not business_weak
            if holding_linkage is ABSENT:
                assert after is RecommendationDirection.BUY
            else:
                # Held: only UNDERVALUED is a reserved cell -- FAIRLY_VALUED
                # + held was already HOLD, never in `changed_cells` at all.
                assert valuation_status is UNDERVALUED
                assert after is RecommendationDirection.ADD

        # And the reserved cells really did change at least once each --
        # confirms this sweep exercises the real decision procedure.
        assert any(after is RecommendationDirection.BUY for _, after in changed_cells.values())
        assert any(after is RecommendationDirection.ADD for _, after in changed_cells.values())


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
            valuation_support_status=VALUATION_SUPPORT_INSUFFICIENT,
            has_portfolio_dampening=False,
            has_high_financial_or_valuation_risk=True,
        )
        assert select_direction(**kwargs) == select_direction(**kwargs) == RecommendationDirection.TRIM

    def test_identical_inputs_produce_identical_results_at_supported(self):
        kwargs = dict(
            holding_linkage=ABSENT,
            business_evaluation_state=EVALUATED,
            valuation_state=EVALUATED,
            portfolio_intelligence_state=EVALUATED,
            reasoning_state=EVALUATED,
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=STRONG,
            capital_allocation_status=MODERATE,
            valuation_status=UNDERVALUED,
            valuation_support_status=SUPPORTED,
            has_portfolio_dampening=False,
            has_high_financial_or_valuation_risk=False,
        )
        assert select_direction(**kwargs) == select_direction(**kwargs) == RecommendationDirection.BUY


# ---------------------------------------------------------------------------
# DE-008 §21 invariant traceability (DE-016 Phase 14) -- each test below is
# named after, and cites, the exact invariant it re-verifies post-DE-016.
# Every one of these is already proven, structurally or behaviorally, by a
# test above; this class exists to make the DE-008 §21 citation explicit
# and searchable, not to introduce new coverage.
# ---------------------------------------------------------------------------


class TestDe008Section21InvariantTraceability:
    def test_invariant_1_buy_requires_business_positive_and_valuation_support_established(self):
        assert _select(holding_linkage=ABSENT, growth_status=STRONG, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED) is RecommendationDirection.BUY
        assert _select(holding_linkage=ABSENT, growth_status=WEAK, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED) is not RecommendationDirection.BUY
        assert _select(holding_linkage=ABSENT, growth_status=STRONG, valuation_status=UNDERVALUED, valuation_support_status=NOT_SUPPORTED) is not RecommendationDirection.BUY

    def test_invariant_2_add_requires_the_same_standard_as_buy(self):
        assert _select(holding_linkage=PRESENT, growth_status=STRONG, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED) is RecommendationDirection.ADD
        assert _select(holding_linkage=PRESENT, growth_status=WEAK, valuation_status=UNDERVALUED, valuation_support_status=SUPPORTED) is not RecommendationDirection.ADD
        assert _select(holding_linkage=PRESENT, growth_status=STRONG, valuation_status=UNDERVALUED, valuation_support_status=NOT_SUPPORTED) is not RecommendationDirection.ADD

    def test_invariant_6_valuation_alone_never_causes_exit(self):
        for valuation_support_status in _VALUATION_SUPPORT_STATUSES:
            sweep = _full_sweep(valuation_support_status)
            assert RecommendationDirection.EXIT not in sweep.values()

    def test_invariant_8_conviction_never_determines_direction(self):
        """Structural, not merely behavioral: `select_direction` has no
        Conviction-level parameter at all -- there is nothing for it to
        branch on."""
        import inspect
        from atlas.analysis_engine.direction_selector import select_direction as fn

        params = inspect.signature(fn).parameters
        assert "conviction" not in params
        assert "conviction_level" not in params

    def test_invariant_9_portfolio_and_risk_never_independently_create_buy_or_add(self):
        result = _select(
            holding_linkage=ABSENT,
            valuation_status=UNDERVALUED,
            valuation_support_status=SUPPORTED,
            has_portfolio_dampening=True,
        )
        assert result is not RecommendationDirection.BUY
        result = _select(
            holding_linkage=PRESENT,
            valuation_status=UNDERVALUED,
            valuation_support_status=SUPPORTED,
            has_high_financial_or_valuation_risk=True,
        )
        assert result is not RecommendationDirection.ADD

    def test_invariant_11_undervalued_is_never_equivalent_to_valuation_support_established(self):
        """`ValuationStatus.UNDERVALUED` alone (`valuation_support_status`
        left at its ordinary, unestablished default) never produces BUY
        or ADD -- re-verified here at the Direction Selection layer;
        proven independently, at the computation layer, by
        `test_support.py::TestArchitecturalBoundary`'s direct source
        check that `evaluate_valuation_support` never reads
        `fcf_yield_finding.status`."""
        assert _select(holding_linkage=ABSENT, valuation_status=UNDERVALUED) is not RecommendationDirection.BUY
        assert _select(holding_linkage=PRESENT, valuation_status=UNDERVALUED) is not RecommendationDirection.ADD
