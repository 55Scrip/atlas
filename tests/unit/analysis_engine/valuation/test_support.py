"""Tests for `atlas.analysis_engine.valuation.support` (Valuation Support
for Capital Deployment -- Alpha implementation sprint).

Five groups, matching the sprint's own required deliverables:

1. `TestUnitConstruction` -- Part 9 unit tests: status/reasoning/gap.
2. `TestArchitecturalBoundary` -- Part 8: Recommendation cannot access
   valuation models/calculations/implementation/reasoning; observes only
   the public contract.
3. `TestRegression` -- Part 9: changing valuation implementation must not
   require Recommendation changes.
4. `TestAdversarialCases` -- Part 10: no data, conflicting data, partial
   data, clearly supportive (`UNDERVALUED`), clearly restrictive
   (`EXPENSIVE`) valuation.
5. `TestMinimality` -- Part 11: every public field is load-bearing; none
   can be removed without losing something the adopted contract requires.

Fixtures reuse `tests.unit.analysis_engine.valuation._fixtures` and the
same real-record-through-`evaluate_valuation` pattern `test_pipeline.py`
already established -- every `ValuationEngineResult` fed to
`evaluate_valuation_support` in this file is a real, computed result, not
a hand-built fake, per this codebase's own "reuse, never re-derive"
discipline.
"""
from __future__ import annotations

import dataclasses
import inspect
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.recommendation import RecommendationDirection, evaluate_recommendation_gate
from atlas.analysis_engine.direction_selector import select_direction
from atlas.analysis_engine.recommendation_conviction import calculate_recommendation_conviction
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.facts import extract_valuation_facts_from_records
from atlas.analysis_engine.valuation.models import ValuationEngineResult
from atlas.analysis_engine.valuation.pipeline import evaluate_valuation
from atlas.analysis_engine.valuation.support import (
    ValuationSupport,
    ValuationSupportGapKind,
    ValuationSupportStatus,
    evaluate_valuation_support,
)
from atlas.decision_engine.contracts import EvaluationState
from tests.unit.analysis_engine.valuation._fixtures import EVALUATED_AT, fundamentals_record, market_record


def _filed(year: int, month: int = 2, day: int = 15) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def _evaluate_support(business_facts, valuation_facts, *, generated_at=EVALUATED_AT) -> ValuationSupport:
    """Thin helper matching the real, post-`DE-015` `evaluate_valuation_support`
    signature -- computes `valuation_engine` fresh and calls through."""
    valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=generated_at)
    return evaluate_valuation_support(valuation_engine, business_facts, valuation_facts, generated_at=generated_at)


def _undervalued_facts():
    """Real records -> a genuine `ValuationStatus.UNDERVALUED`
    `FCF_YIELD_RELATIVE` finding -- identical fixture shape
    `test_pipeline.py::TestEndToEndFromRealRecords` already established.
    Deliberately only 3 fundamental periods -- too thin for even one
    4-year rolling growth window, so the Scenario path stays ineligible
    regardless of `FCF_YIELD_RELATIVE`'s own status."""
    records = (
        fundamentals_record(period_end=date(2022, 12, 31), identifier="uv22", published_at=_filed(2023), free_cash_flow=100.0),
        fundamentals_record(period_end=date(2023, 12, 31), identifier="uv23", published_at=_filed(2024), free_cash_flow=110.0),
        fundamentals_record(period_end=date(2024, 12, 31), identifier="uv24", published_at=_filed(2025), free_cash_flow=200.0),
        market_record(period_end=date(2023, 3, 1), identifier="uvm22", share_price=50.0, shares_outstanding=100.0),
        market_record(period_end=date(2024, 3, 1), identifier="uvm23", share_price=52.0, shares_outstanding=100.0),
        market_record(period_end=date(2025, 3, 1), identifier="uvm24", share_price=53.0, shares_outstanding=100.0),
    )
    business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
    fcf_yield = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
    assert fcf_yield.status is ValuationStatus.UNDERVALUED
    return business_facts, valuation_facts


def _expensive_facts():
    """Identical shape to `test_pipeline.py::TestScenarioE`'s own
    real-records-produce-`EXPENSIVE` fixture -- same thin, 3-period
    history, so the Scenario path stays ineligible here too."""
    records = (
        fundamentals_record(period_end=date(2022, 12, 31), identifier="ex22", published_at=_filed(2023), free_cash_flow=100.0),
        fundamentals_record(period_end=date(2023, 12, 31), identifier="ex23", published_at=_filed(2024), free_cash_flow=150.0),
        fundamentals_record(period_end=date(2024, 12, 31), identifier="ex24", published_at=_filed(2025), free_cash_flow=250.0),
        market_record(period_end=date(2023, 3, 1), identifier="exm22", share_price=10.0, shares_outstanding=100.0),
        market_record(period_end=date(2024, 3, 1), identifier="exm23", share_price=10.0, shares_outstanding=100.0),
        market_record(period_end=date(2025, 3, 1), identifier="exm24", share_price=90.0, shares_outstanding=100.0),
    )
    business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
    fcf_yield = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
    assert fcf_yield.status is ValuationStatus.EXPENSIVE
    return business_facts, valuation_facts


def _fairly_valued_facts():
    """Steady price, steady FCF -- current yield lands strictly between
    the two historical extremes -> `FAIRLY_VALUED`. Same thin history."""
    records = (
        fundamentals_record(period_end=date(2022, 12, 31), identifier="fv22", published_at=_filed(2023), free_cash_flow=90.0),
        fundamentals_record(period_end=date(2023, 12, 31), identifier="fv23", published_at=_filed(2024), free_cash_flow=100.0),
        fundamentals_record(period_end=date(2024, 12, 31), identifier="fv24", published_at=_filed(2025), free_cash_flow=95.0),
        market_record(period_end=date(2023, 3, 1), identifier="fvm22", share_price=40.0, shares_outstanding=100.0),
        market_record(period_end=date(2024, 3, 1), identifier="fvm23", share_price=60.0, shares_outstanding=100.0),
        market_record(period_end=date(2025, 3, 1), identifier="fvm24", share_price=50.0, shares_outstanding=100.0),
    )
    business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
    fcf_yield = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
    assert fcf_yield.status is ValuationStatus.FAIRLY_VALUED
    return business_facts, valuation_facts


def _no_data_facts():
    """No records at all -- `FCF_YIELD_RELATIVE` itself is
    `INSUFFICIENT_INPUT`, and so are the three scenario methods (their
    permanent state)."""
    business_facts: tuple = ()
    valuation_facts: tuple = ()
    valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
    fcf_yield = next(f for f in valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE)
    assert fcf_yield.status is ValuationStatus.INSUFFICIENT_INPUT
    return business_facts, valuation_facts


def _single_observation_facts():
    """Partial data -- one real market observation, no historical range
    to compare it against (`Insufficient Historical Valuation Periods`)."""
    records = (
        fundamentals_record(period_end=date(2024, 12, 31), identifier="so24", published_at=_filed(2025), free_cash_flow=100.0),
        market_record(period_end=date(2025, 3, 1), identifier="som24", share_price=50.0, shares_outstanding=100.0),
    )
    business_facts = extract_facts_from_records(records, evaluated_at=EVALUATED_AT)
    valuation_facts = extract_valuation_facts_from_records(records, evaluated_at=EVALUATED_AT)
    return business_facts, valuation_facts


# ---------------------------------------------------------------------------
# 1. Unit construction (Part 9)
# ---------------------------------------------------------------------------


class TestUnitConstruction:
    def test_valid_supported_construction(self):
        support = ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning="A real reason.")
        assert support.status is ValuationSupportStatus.SUPPORTED
        assert support.gap is None

    def test_valid_not_supported_construction(self):
        support = ValuationSupport(status=ValuationSupportStatus.NOT_SUPPORTED, reasoning="A real reason.")
        assert support.status is ValuationSupportStatus.NOT_SUPPORTED
        assert support.gap is None

    def test_valid_insufficient_input_construction_requires_gap(self):
        support = ValuationSupport(
            status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            reasoning="A real reason.",
            gap=ValuationSupportGapKind.MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT,
        )
        assert support.gap is ValuationSupportGapKind.MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT

    def test_insufficient_input_without_gap_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(status=ValuationSupportStatus.INSUFFICIENT_INPUT, reasoning="A real reason.")

    def test_supported_with_gap_is_rejected(self):
        """Gap only explains INSUFFICIENT_INPUT -- never accompanies a
        real conclusion."""
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(
                status=ValuationSupportStatus.SUPPORTED,
                reasoning="A real reason.",
                gap=ValuationSupportGapKind.MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT,
            )

    def test_not_supported_with_gap_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(
                status=ValuationSupportStatus.NOT_SUPPORTED,
                reasoning="A real reason.",
                gap=ValuationSupportGapKind.MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT,
            )

    def test_empty_reasoning_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning="")

    def test_blank_reasoning_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning="   ")

    def test_bare_string_status_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(status="supported", reasoning="A real reason.")

    def test_bare_string_gap_is_rejected(self):
        with pytest.raises(AnalysisEngineContractError):
            ValuationSupport(
                status=ValuationSupportStatus.INSUFFICIENT_INPUT,
                reasoning="A real reason.",
                gap="missing_capital_deployment_valuation_support",
            )

    def test_exactly_three_status_members(self):
        assert {m.value for m in ValuationSupportStatus} == {"supported", "not_supported", "insufficient_input"}

    def test_immutable(self):
        support = ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning="A real reason.")
        with pytest.raises(dataclasses.FrozenInstanceError):
            support.status = ValuationSupportStatus.NOT_SUPPORTED  # type: ignore[misc]

    def test_evaluate_valuation_support_is_deterministic(self):
        business_facts, valuation_facts = _undervalued_facts()
        assert _evaluate_support(business_facts, valuation_facts) == _evaluate_support(business_facts, valuation_facts)


# ---------------------------------------------------------------------------
# 2. Architectural boundary (Part 8)
# ---------------------------------------------------------------------------


class TestArchitecturalBoundary:
    """Revised for `DE-016`: `select_direction`/`evaluate_recommendation_gate`
    now deliberately reference `ValuationSupport` (`DE-008`'s own,
    previously-unreachable BUY/ADD prerequisite, now real per `DE-015`)
    -- but never `evaluate_valuation_support` (the computation, which
    stays exclusively `pipeline.py`'s to call), and never
    `.reasoning`/`.gap` (`DE-015` §18's own public-status-only
    constraint). `recommendation_conviction.py` remains, correctly,
    fully untouched -- see `DE-016`'s own Phase 10."""

    def test_recommendation_module_references_the_type_never_the_computation(self):
        """`recommendation.py` may name `ValuationSupport` (the type it
        now accepts as a parameter) but must never import or call
        `evaluate_valuation_support` -- computing Valuation Support stays
        exclusively `pipeline.py`'s job."""
        import atlas.analysis_engine.recommendation as module

        assert hasattr(module, "ValuationSupport")
        assert not hasattr(module, "evaluate_valuation_support")

    def test_direction_selector_module_references_only_the_status_enum(self):
        """`direction_selector.py` may name `ValuationSupportStatus` (the
        public enum it now accepts) but never the full `ValuationSupport`
        object (which would expose `.reasoning`/`.gap`) and never the
        computation function -- checked against the real, imported
        namespace (never against raw text, where `ValuationSupportStatus`
        would trivially satisfy a substring check for `ValuationSupport`
        too)."""
        import atlas.analysis_engine.direction_selector as module

        assert hasattr(module, "ValuationSupportStatus")
        assert not hasattr(module, "ValuationSupport")
        assert not hasattr(module, "evaluate_valuation_support")

    def test_recommendation_conviction_module_does_not_reference_valuation_support(self):
        """Unchanged by `DE-016`: Recommendation Conviction (`DE-004`
        §3) remains completely independent -- a Direction prerequisite
        is never Conviction evidence (`DE-016` Phase 10)."""
        import atlas.analysis_engine.recommendation_conviction as module

        source = inspect.getsource(module)
        for forbidden in ("ValuationSupport", "evaluate_valuation_support", "valuation.support"):
            assert forbidden not in source

    def test_select_direction_signature_has_the_status_parameter_only(self):
        params = inspect.signature(select_direction).parameters
        assert "valuation_support_status" in params
        assert "valuation_support_reasoning" not in params
        assert "valuation_support_gap" not in params

    def test_evaluate_recommendation_gate_signature_has_valuation_support_parameter(self):
        params = inspect.signature(evaluate_recommendation_gate).parameters
        assert "valuation_support" in params

    def test_neither_function_reads_reasoning_or_gap_from_the_source(self):
        """`DE-015` §18: only the public `status` field crosses the
        boundary. Checked against real source, not behavior alone."""
        import pathlib

        for fn in (select_direction, evaluate_recommendation_gate):
            path = pathlib.Path(inspect.getfile(fn))
            source = path.read_text(encoding="utf-8")
            assert "valuation_support.reasoning" not in source
            assert "valuation_support.gap" not in source

    def test_calculate_recommendation_conviction_signature_has_no_valuation_support_parameter(self):
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert not any("valuation_support" in name for name in params)

    def test_public_contract_exposes_only_status_reasoning_gap(self):
        """`ValuationSupport` never leaks a `ValuationFinding`,
        `ValuationEngineResult`, `ValuationMethodKind`, or any raw
        valuation-model type through any of its own fields."""
        field_names = {f.name for f in dataclasses.fields(ValuationSupport)}
        assert field_names == {"status", "reasoning", "gap"}
        field_types = {f.name: f.type for f in dataclasses.fields(ValuationSupport)}
        for forbidden in ("ValuationFinding", "ValuationEngineResult", "ValuationMethodKind", "ValuationStatus"):
            for declared_type in field_types.values():
                assert forbidden not in str(declared_type)

    def test_reasoning_never_names_a_valuation_model_or_formula(self):
        """Part 6's own explicit prohibition, checked against every real
        reasoning string this module can currently produce."""
        forbidden_terms = (
            "DCF", "EV/EBIT", "EV/EBITDA", "PEG", "Residual Income",
            "FCF yield", "fcf_yield", "discounted cash flow", "P/E",
            "formula", "calculation",
        )
        for business_facts, valuation_facts in (
            _undervalued_facts(), _expensive_facts(), _fairly_valued_facts(), _no_data_facts()
        ):
            support = _evaluate_support(business_facts, valuation_facts)
            for term in forbidden_terms:
                assert term.lower() not in support.reasoning.lower()

    def test_evaluate_recommendation_gate_still_produces_a_result_with_a_real_valuation_support(self):
        """Recommendation's own gate function runs to completion given a
        real, freshly-computed `ValuationSupport` (`DE-016`'s own
        required wiring) -- an `INSUFFICIENT_INPUT` one here, since this
        fixture's business-inconclusive shape is not exercising the new
        BUY/ADD path (that lives in
        `test_recommendation.py::TestBuyAddNowWired`)."""
        from tests.unit.analysis_engine._fixtures import run_populated

        engine_input, output = run_populated()
        from atlas.analysis_engine.business import evaluate_business_analysis
        from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel

        business_analysis = evaluate_business_analysis(output.business_evaluation, business_records=(), evaluated_at=EVALUATED_AT)
        result = evaluate_recommendation_gate(
            engine_input,
            business_evaluation=output.business_evaluation,
            valuation=output.valuation,
            portfolio_intelligence=output.portfolio_intelligence,
            reasoning=output.reasoning,
            conviction=ConvictionAssessment(level=ConvictionLevel.MODERATE, reasons=()),
            business_analysis=business_analysis,
            valuation_engine=evaluate_valuation((), (), evaluated_at=EVALUATED_AT),
            valuation_support=ValuationSupport(
                status=ValuationSupportStatus.INSUFFICIENT_INPUT,
                reasoning="No real data supplied in this fixture.",
                gap=ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA,
            ),
            has_high_financial_or_valuation_risk=False,
            has_open_questions=False,
            generated_at=EVALUATED_AT,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# 3. Regression: changing valuation implementation must not require
#    Recommendation changes (Part 9)
# ---------------------------------------------------------------------------


class TestRegression:
    def test_valuation_support_implementation_changes_flow_through_status_only(self):
        """Revised for `DE-016`: `select_direction` now deliberately
        reads `valuation_support_status` (`DE-015` §18's own public
        contract), so it is no longer invariant to `ValuationSupport`'s
        *content* -- that invariance claim is retired on purpose (see
        `DE-016`). What Part 9's original regression guarantee still
        protects, and what this test now proves instead: `select_direction`
        never calls `evaluate_valuation_support` itself, and the *shape*
        of the wiring is exactly "compute once elsewhere, pass `.status`
        through" -- a future change to valuation's own internal
        implementation (this function's body) still cannot require any
        change to `select_direction`'s own code, only to the `.status`
        value it is handed."""
        from atlas.decision_engine.contracts import EvidenceCoverageLevel, HoldingLinkage
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus

        # select_direction never calls the computation itself -- the
        # patch target is never hit, confirming the call graph directly.
        assert "evaluate_valuation_support" not in inspect.getsource(select_direction)

        kwargs = dict(
            holding_linkage=HoldingLinkage.ABSENT,
            business_evaluation_state=EvaluationState.EVALUATED,
            valuation_state=EvaluationState.EVALUATED,
            portfolio_intelligence_state=EvaluationState.EVALUATED,
            reasoning_state=EvaluationState.EVALUATED,
            evidence_coverage=EvidenceCoverageLevel.FULL,
            growth_status=BusinessCategoryStatus.MODERATE,
            capital_allocation_status=BusinessCategoryStatus.INSUFFICIENT_INPUT,
            valuation_status=ValuationStatus.UNDERVALUED,
            has_portfolio_dampening=False,
            has_high_financial_or_valuation_risk=False,
        )
        # A hypothetical future `evaluate_valuation_support` returning
        # SUPPORTED, read only through its own public `.status` -- no
        # other change to select_direction's own inputs.
        hypothetical = ValuationSupport(status=ValuationSupportStatus.SUPPORTED, reasoning="hypothetical")
        before = select_direction(**kwargs, valuation_support_status=ValuationSupportStatus.INSUFFICIENT_INPUT)
        after = select_direction(**kwargs, valuation_support_status=hypothetical.status)
        assert before is None
        assert after is RecommendationDirection.BUY

    def test_pipeline_recommendation_unaffected_by_valuation_support_content(self):
        """Integration-level proof of `DE-016`'s own "collapse" guarantee
        (Phase 6/11): `INSUFFICIENT_INPUT` and `NOT_SUPPORTED` are
        deliberately indistinguishable to Direction Selection -- neither
        establishes the Capital Deployment prerequisite, and `DE-008`
        assigns `NOT_SUPPORTED` no independent TRIM/EXIT role. Patches
        `evaluate_valuation_support` (as `pipeline.py` imports it) to
        swap between the two and confirms `CanonicalAnalysis.recommendation`
        -- computed through the real `assemble_analysis` entry point --
        is byte-identical either way. This is no longer "Recommendation
        is unaffected by ValuationSupport" (false since `DE-016`; see
        `TestRegression` above and `test_recommendation.py
        ::TestBuyAddNowWired` for the real, now-affecting `SUPPORTED`
        case) -- it is the narrower, still-true claim that these two
        *specific* statuses remain behaviorally identical."""
        from atlas.analysis_engine.pipeline import assemble_analysis
        from tests.unit.analysis_engine._fixtures import run_populated

        engine_input, decision_output = run_populated()

        real = ValuationSupport(
            status=ValuationSupportStatus.INSUFFICIENT_INPUT,
            reasoning="real",
            gap=ValuationSupportGapKind.MISSING_CAPITAL_DEPLOYMENT_VALUATION_SUPPORT,
        )
        hypothetical = ValuationSupport(status=ValuationSupportStatus.NOT_SUPPORTED, reasoning="hypothetical")

        with patch("atlas.analysis_engine.pipeline.evaluate_valuation_support", return_value=real):
            analysis_real = assemble_analysis(engine_input, decision_output, is_thesis_stale=False, generated_at=EVALUATED_AT)
        with patch("atlas.analysis_engine.pipeline.evaluate_valuation_support", return_value=hypothetical):
            analysis_hypothetical = assemble_analysis(engine_input, decision_output, is_thesis_stale=False, generated_at=EVALUATED_AT)

        assert analysis_real.recommendation == analysis_hypothetical.recommendation
        assert analysis_real.conviction == analysis_hypothetical.conviction
        assert analysis_real.valuation_support != analysis_hypothetical.valuation_support


# ---------------------------------------------------------------------------
# 4. Adversarial cases (Part 10)
# ---------------------------------------------------------------------------


class TestAdversarialCases:
    """`DE-015` implementation sprint: these fixtures are all deliberately
    too thin (3 fundamental periods -- fewer than the 4-year rolling
    window needs to form even one growth observation) for the Scenario
    path to ever become eligible, and carry no `CASH`/`TOTAL_DEBT` facts
    for the Net-Cash path either -- so every case here still resolves to
    `INSUFFICIENT_INPUT`, but now because real evaluation genuinely finds
    no sufficient proof, not because the function is a constant stub.
    The central claims from the prior sprint remain intact and are
    re-verified against real execution: `UNDERVALUED`/`EXPENSIVE`/
    `FAIRLY_VALUED` alone, on their own, never automatically produce
    `SUPPORTED`/`NOT_SUPPORTED`."""

    def test_no_valuation_data_is_insufficient_input(self):
        business_facts, valuation_facts = _no_data_facts()
        support = _evaluate_support(business_facts, valuation_facts)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is ValuationSupportGapKind.INSUFFICIENT_HISTORICAL_VALUATION_DATA

    def test_partial_valuation_data_is_insufficient_input(self):
        business_facts, valuation_facts = _single_observation_facts()
        support = _evaluate_support(business_facts, valuation_facts)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT

    def test_clearly_supportive_looking_valuation_undervalued_does_not_automatically_produce_supported(self):
        """The central adversarial case: `UNDERVALUED` -- the most
        favorable real conclusion `FCF_YIELD_RELATIVE` can produce --
        does NOT, by itself, become `SUPPORTED`. This is `DE-008` §21
        invariant 11 and `DE-015` §20 rejected alternative 1, verified
        against a real, genuinely `UNDERVALUED` result whose Scenario/
        Net-Cash paths independently have nothing else to go on."""
        business_facts, valuation_facts = _undervalued_facts()
        support = _evaluate_support(business_facts, valuation_facts)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.status is not ValuationSupportStatus.SUPPORTED

    def test_clearly_restrictive_looking_valuation_expensive_does_not_automatically_produce_not_supported(self):
        """The symmetric adversarial case: `EXPENSIVE` does NOT, by
        itself, become `NOT_SUPPORTED` either -- see `support.py`'s own
        module docstring for the full reasoning."""
        business_facts, valuation_facts = _expensive_facts()
        support = _evaluate_support(business_facts, valuation_facts)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.status is not ValuationSupportStatus.NOT_SUPPORTED

    def test_fairly_valued_is_also_insufficient_input(self):
        business_facts, valuation_facts = _fairly_valued_facts()
        support = _evaluate_support(business_facts, valuation_facts)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT

    def test_conflicting_scenario_method_kinds_still_resolve_honestly(self):
        """'Conflicting' evidence here means the one real method
        (`FCF_YIELD_RELATIVE`) and the three scenario placeholders
        disagree in kind -- one has a real conclusion, the others are
        honestly gapped. This alone is not the `CONFLICTING_VALUATION_PROOFS`
        case (`DE-015` §16's own, different meaning of conflict, between
        two *sufficient* proofs) -- verified here to keep the two
        concepts distinct."""
        business_facts, valuation_facts = _undervalued_facts()
        valuation_engine = evaluate_valuation(business_facts, valuation_facts, evaluated_at=EVALUATED_AT)
        kinds_and_statuses = {f.kind: f.status for f in valuation_engine.findings}
        assert kinds_and_statuses[ValuationMethodKind.FCF_YIELD_RELATIVE] is ValuationStatus.UNDERVALUED
        assert kinds_and_statuses[ValuationMethodKind.SCENARIO_BEAR] is ValuationStatus.INSUFFICIENT_INPUT
        support = _evaluate_support(business_facts, valuation_facts)
        assert support.status is ValuationSupportStatus.INSUFFICIENT_INPUT
        assert support.gap is not ValuationSupportGapKind.CONFLICTING_VALUATION_PROOFS


# ---------------------------------------------------------------------------
# 5. Minimality verification (Part 11)
# ---------------------------------------------------------------------------


class TestMinimality:
    def test_status_cannot_be_removed(self):
        """Without `status`, the object could not answer the one
        question it exists to answer -- there would be nothing for a
        consumer to observe at all."""
        field_names = {f.name for f in dataclasses.fields(ValuationSupport)}
        assert "status" in field_names

    def test_reasoning_cannot_be_removed(self):
        """Without `reasoning`, `INSUFFICIENT_INPUT` (the only status
        Alpha ever produces) would be unexplained -- a bare enum value
        with no way for a reader to learn why, violating this codebase's
        own "never a silent gap" discipline that every sibling gap-shaped
        type already follows (`OutlookGapKind`, `ValuationDataGapKind`)."""
        field_names = {f.name for f in dataclasses.fields(ValuationSupport)}
        assert "reasoning" in field_names

    def test_gap_cannot_be_removed(self):
        """Without `gap`, `INSUFFICIENT_INPUT` would carry only free-text
        `reasoning` -- fine for a human reader, but not a stable,
        programmatically-branchable reason a future consumer (or this
        sprint's own adversarial tests) could depend on. `gap` is what
        keeps `INSUFFICIENT_INPUT` a *named*, not merely *described*,
        outcome."""
        field_names = {f.name for f in dataclasses.fields(ValuationSupport)}
        assert "gap" in field_names

    def test_no_field_beyond_the_adopted_three_exists(self):
        """The other direction of minimality: nothing extra crept in --
        no confidence, score, probability, weighting, ranking, or
        conviction field."""
        field_names = {f.name for f in dataclasses.fields(ValuationSupport)}
        forbidden = {"confidence", "score", "probability", "weight", "weighting", "ranking", "conviction"}
        assert field_names.isdisjoint(forbidden)

    def test_gap_kind_widened_additively_never_by_removal(self):
        """`DE-015` implementation sprint: the original Alpha-stub-era
        member is still present (no removals, no renames); five real,
        additive members were required to make every real
        `INSUFFICIENT_INPUT` outcome the real evaluator can now produce
        non-silent (see `support.py`'s own `ValuationSupportGapKind`
        docstring)."""
        members = {m.value for m in ValuationSupportGapKind}
        assert "missing_capital_deployment_valuation_support" in members
        assert len(members) == 6
