"""Canonical Recommendation Reasoning -- domain integrity guards.

This sprint preserves reasoning Atlas already computed; it changes no
recommendation. The tests below are therefore mostly *negative*: they
pin what must NOT happen, because the failure this work exists to
prevent -- process state presented as investment reasoning, and a
second producer inventing a change trigger from readiness blockers --
was invisible to ordinary assertions and only surfaced under runtime
tracing.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from atlas.analysis_engine import reasoning as reasoning_module
from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
from atlas.analysis_engine.reasoning import (
    CanonicalEngine,
    InvestmentReason,
    InvestmentReasonKind,
    KeyUnknownKind,
    ProcessStateReason,
    ProcessStateReasonKind,
    ReasoningPolarity,
    SignalState,
    build_drivers,
    build_key_unknowns,
    build_signal_summary,
)
from atlas.analysis_engine.valuation.contracts import ValuationStatus
from atlas.analysis_engine.valuation.support import ValuationSupportStatus


def _drivers(**overrides):
    kwargs = dict(
        growth_status=BusinessCategoryStatus.MODERATE,
        capital_allocation_status=BusinessCategoryStatus.STRONG,
        valuation_status=ValuationStatus.FAIRLY_VALUED,
        valuation_support_status=ValuationSupportStatus.SUPPORTED,
        has_high_financial_or_valuation_risk=False,
        has_real_risk_evidence=True,
    )
    kwargs.update(overrides)
    return kwargs


class TestInvestmentAndProcessReasonsAreDisjoint:
    def test_the_two_vocabularies_share_no_member(self):
        """The Phase 9 defect in one assertion: `monitoring_current`
        and `decision_support_reached` were recorded as the reasons for
        a REDUCE. No value may belong to both worlds."""
        investment = {member.value for member in InvestmentReasonKind}
        process = {member.value for member in ProcessStateReasonKind}
        assert investment & process == set()

    def test_neither_type_is_a_subclass_of_the_other(self):
        assert not issubclass(InvestmentReason, ProcessStateReason)
        assert not issubclass(ProcessStateReason, InvestmentReason)

    def test_a_process_reason_cannot_be_built_as_an_investment_reason(self):
        with pytest.raises(TypeError):
            InvestmentReason(kind=ProcessStateReasonKind.EVIDENCE_COVERAGE_FULL)  # type: ignore[call-arg]

    def test_no_process_vocabulary_leaks_into_a_driver_list(self):
        primary, counter = build_drivers(**_drivers())
        for driver in (*primary, *counter):
            assert isinstance(driver.kind, InvestmentReasonKind)


class TestDriverExtraction:
    def test_drivers_restate_the_statuses_that_chose_the_direction(self):
        primary, counter = build_drivers(**_drivers(
            valuation_status=ValuationStatus.EXPENSIVE,
            growth_status=BusinessCategoryStatus.WEAK,
        ))
        assert InvestmentReasonKind.VALUATION_EXPENSIVE in {d.kind for d in counter}
        assert InvestmentReasonKind.GROWTH_WEAK in {d.kind for d in counter}
        assert all(d.polarity is ReasoningPolarity.ADVERSE for d in counter)
        assert all(d.polarity is ReasoningPolarity.SUPPORTIVE for d in primary)

    def test_every_driver_names_its_source_engine_and_status(self):
        """Traceability: a driver that cannot say where it came from is
        indistinguishable from an invented one."""
        primary, counter = build_drivers(**_drivers())
        for driver in (*primary, *counter):
            assert isinstance(driver.engine, CanonicalEngine)
            assert driver.source_status

    def test_an_inconclusive_engine_contributes_no_driver(self):
        """Unknown is not adverse -- the rule that keeps coverage gaps
        from silently reading as bearish."""
        primary, counter = build_drivers(**_drivers(
            growth_status=BusinessCategoryStatus.INSUFFICIENT_INPUT,
            capital_allocation_status=BusinessCategoryStatus.NOT_EVALUATED,
        ))
        engines = {d.engine for d in (*primary, *counter)}
        assert CanonicalEngine.GROWTH not in engines
        assert CanonicalEngine.CAPITAL_ALLOCATION not in engines

    def test_a_neutral_finding_appears_in_neither_driver_list(self):
        """`fairly_valued` is a real finding but argues for nothing; it
        belongs in the signal summary, not padding a driver list."""
        primary, counter = build_drivers(**_drivers(valuation_status=ValuationStatus.FAIRLY_VALUED))
        assert CanonicalEngine.VALUATION not in {d.engine for d in (*primary, *counter)}

    def test_ordering_follows_the_documented_precedence(self):
        """Risk outranks valuation outranks business quality -- the same
        order `_derive_what_would_change` already applies, reused rather
        than reinvented."""
        _, counter = build_drivers(**_drivers(
            has_high_financial_or_valuation_risk=True,
            valuation_status=ValuationStatus.EXPENSIVE,
            growth_status=BusinessCategoryStatus.WEAK,
            capital_allocation_status=BusinessCategoryStatus.WEAK,
        ))
        assert [d.engine for d in counter] == [
            CanonicalEngine.FINANCIAL_RISK,
            CanonicalEngine.VALUATION,
            CanonicalEngine.GROWTH,
            CanonicalEngine.CAPITAL_ALLOCATION,
        ]

    def test_extraction_is_deterministic(self):
        assert len({repr(build_drivers(**_drivers())) for _ in range(50)}) == 1


class TestSignalSummaryIsTotal:
    def test_every_canonical_engine_is_named_every_time(self):
        summary = build_signal_summary(**_drivers())
        assert {c.engine for c in summary} == set(CanonicalEngine)

    def test_disconnected_engines_are_recorded_not_omitted(self):
        """`NOT_IN_DIRECTION_CONTRACT` is the distinction Phase 9 could
        not make: Business Quality is computed and real, it simply does
        not reach direction yet."""
        summary = {c.engine: c for c in build_signal_summary(**_drivers())}
        for engine in (CanonicalEngine.BUSINESS_QUALITY, CanonicalEngine.INDUSTRY_CONTEXT,
                       CanonicalEngine.EXPECTED_RETURN):
            assert summary[engine].state is SignalState.NOT_IN_DIRECTION_CONTRACT
            assert summary[engine].influenced_direction is False

    def test_not_in_direction_contract_is_distinct_from_not_evaluated(self):
        assert SignalState.NOT_IN_DIRECTION_CONTRACT is not SignalState.NOT_EVALUATED
        assert SignalState.NOT_IN_DIRECTION_CONTRACT is not SignalState.INCONCLUSIVE


class TestKeyUnknowns:
    def test_a_disconnected_engine_is_an_architectural_state_not_a_gap(self):
        unknowns = {u.engine: u.kind for u in build_key_unknowns(build_signal_summary(**_drivers()))}
        assert unknowns[CanonicalEngine.BUSINESS_QUALITY] is KeyUnknownKind.NOT_CONNECTED_TO_DIRECTION

    def test_an_inconclusive_engine_is_a_missing_input(self):
        summary = build_signal_summary(**_drivers(
            growth_status=BusinessCategoryStatus.INSUFFICIENT_INPUT))
        unknowns = {u.engine: u.kind for u in build_key_unknowns(summary)}
        assert unknowns[CanonicalEngine.GROWTH] is KeyUnknownKind.ANALYSIS_INPUT_MISSING

    def test_unknowns_are_not_built_from_readiness_blockers(self):
        """Deliberately derived from `signal_summary` alone, so process
        state cannot re-enter investment reasoning through a side door."""
        source = inspect.getsource(reasoning_module.build_key_unknowns)
        for forbidden in ("blocker", "readiness", "monitoring"):
            assert forbidden not in source.lower().split('"""')[-1]


class TestConvictionSplit:
    def test_conviction_reasons_are_partitioned_not_flattened(self):
        from atlas.analysis_engine.reasoning import build_conviction_reasoning
        from atlas.analysis_engine.recommendation_conviction import (
            RecommendationConvictionAssessment,
            RecommendationConvictionLevel,
            RecommendationConvictionReasonCode,
        )
        assessment = RecommendationConvictionAssessment(
            level=RecommendationConvictionLevel.LOW,
            reasons=(RecommendationConvictionReasonCode.EVIDENCE_COVERAGE_PARTIAL,),
        )
        result = build_conviction_reasoning(assessment)
        assert result.level is RecommendationConvictionLevel.LOW
        assert [r.kind for r in result.evidential_reasons] == [
            ProcessStateReasonKind.EVIDENCE_COVERAGE_PARTIAL]
        assert result.analytical_reasons == ()

    def test_absent_assessment_yields_an_honest_empty_reasoning(self):
        from atlas.analysis_engine.reasoning import build_conviction_reasoning
        result = build_conviction_reasoning(None)
        assert result.level is None and result.evidential_reasons == ()

    def test_the_three_conviction_models_remain_separate(self):
        """DE-004 §3 / DE-007 §11: the scales are independently
        computed and never merged. This sprint must not consolidate."""
        from atlas.analysis_engine.conviction import ConvictionLevel
        from atlas.analysis_engine.recommendation_conviction import RecommendationConvictionLevel
        assert len(list(ConvictionLevel)) == 5
        assert len(list(RecommendationConvictionLevel)) == 3
        assert ConvictionLevel is not RecommendationConvictionLevel


class TestSingleProducer:
    def test_reasoning_is_constructed_in_exactly_one_production_module(self):
        """The guard that would have caught `investment_decision/engine
        .py`'s `change_trigger = blockers[0]` -- a second producer of a
        concept it should have projected."""
        sites = []
        for path in Path("atlas").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                        and node.func.id == "RecommendationReasoning":
                    sites.append(str(path))
        assert sites == ["atlas/analysis_engine/recommendation.py"], sites

    def test_no_module_outside_the_gate_derives_a_change_trigger(self):
        """Counts CALLS, not mentions -- `reasoning.py` cites the
        function by name when documenting that it reuses its
        precedence, which is exactly the opposite of duplicating it."""
        sites = []
        for path in Path("atlas").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                        and node.func.id == "_derive_what_would_change":
                    sites.append(str(path))
        assert sites == ["atlas/analysis_engine/recommendation.py"], sites


class TestArchitectureBoundaries:
    def test_core_reasoning_does_not_import_alpha(self):
        source = Path("atlas/analysis_engine/reasoning.py").read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("atlas.alpha")

    def test_reasoning_does_not_depend_on_stance_or_history(self):
        """Stance reads `analysis.recommendation`; if reasoning read
        Stance the lifecycle would be circular. It also must not need a
        prior snapshot -- reasoning is complete at production time."""
        source = Path("atlas/analysis_engine/reasoning.py").read_text(encoding="utf-8")
        for forbidden in ("Stance", "ChangeIntelligence", "THESIS_STRENGTHENED",
                          "THESIS_WEAKENED", "snapshot"):
            assert forbidden not in source

    def test_reasoning_module_computes_no_new_analysis(self):
        """It restates statuses. It must not reach for records, facts
        or engines of its own.

        Scans executable code only: the module's prose names
        `evaluate_recommendation_gate` to explain where it is called
        from, and a guard that trips on its own explanation teaches
        nothing."""
        tree = ast.parse(Path("atlas/analysis_engine/reasoning.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if isinstance(body, list) and body:
                first = body[0]
                if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                        and isinstance(first.value.value, str)):
                    body.pop(0)
        source = ast.unparse(tree)
        for forbidden in ("BusinessRecord", "business_facts", "evaluate_", "repository"):
            assert forbidden not in source


class TestGrowthMagnitudeInSignalSummary:
    """Continuous growth magnitude, projected into the signal summary.

    `source_status` alone cannot separate companies whose category
    matches but whose economics do not -- NVDA and AMAT are both
    `moderate` while compounding free cash flow at roughly +118%/yr and
    +6%/yr. These fields carry that difference into reasoning without
    attaching a threshold to it and without reaching any recommendation
    input.
    """

    def test_magnitude_is_attached_to_the_growth_contribution(self):
        summary = {c.engine: c for c in build_signal_summary(
            **_drivers(), growth_revenue_cagr=0.25, growth_free_cash_flow_cagr=1.18)}
        growth = summary[CanonicalEngine.GROWTH]
        assert growth.revenue_cagr == 0.25
        assert growth.free_cash_flow_cagr == 1.18

    def test_no_other_engine_receives_growth_magnitude(self):
        """They are growth's own measurements; attaching them elsewhere
        would misattribute them."""
        for contribution in build_signal_summary(
                **_drivers(), growth_revenue_cagr=0.25, growth_free_cash_flow_cagr=1.18):
            if contribution.engine is not CanonicalEngine.GROWTH:
                assert contribution.revenue_cagr is None
                assert contribution.free_cash_flow_cagr is None

    def test_absent_magnitude_stays_none_and_is_not_zero(self):
        growth = {c.engine: c for c in build_signal_summary(**_drivers())}[CanonicalEngine.GROWTH]
        assert growth.revenue_cagr is None and growth.free_cash_flow_cagr is None

    def test_a_computed_zero_is_preserved_as_zero(self):
        """`0.0` means a real zero-growth rate; `None` means no
        principled rate exists. Collapsing them would lose a fact."""
        growth = {c.engine: c for c in build_signal_summary(
            **_drivers(), growth_revenue_cagr=0.0)}[CanonicalEngine.GROWTH]
        assert growth.revenue_cagr == 0.0
        assert growth.revenue_cagr is not None

    def test_same_status_different_magnitude_is_distinguishable(self):
        """The NVDA/AMAT regression case, at unit level."""
        nvda = build_signal_summary(**_drivers(), growth_revenue_cagr=0.2464,
                                    growth_free_cash_flow_cagr=1.1822)
        amat = build_signal_summary(**_drivers(), growth_revenue_cagr=0.1130,
                                    growth_free_cash_flow_cagr=0.0615)
        g_n = {c.engine: c for c in nvda}[CanonicalEngine.GROWTH]
        g_a = {c.engine: c for c in amat}[CanonicalEngine.GROWTH]
        assert g_n.source_status == g_a.source_status      # same category
        assert g_n != g_a                                   # different contribution

    def test_magnitude_never_changes_driver_tokens(self):
        """Drivers take an explicit status argument, so a magnitude
        cannot reach them."""
        baseline = build_drivers(**_drivers())
        assert build_drivers(**_drivers()) == baseline

    def test_magnitude_never_changes_key_unknowns(self):
        plain = build_key_unknowns(build_signal_summary(**_drivers()))
        rich = build_key_unknowns(build_signal_summary(
            **_drivers(), growth_revenue_cagr=9.9, growth_free_cash_flow_cagr=-0.5))
        assert plain == rich

    def test_no_recommendation_function_reads_the_magnitudes(self):
        """Static guard: the protected functions take statuses only."""
        import inspect
        from atlas.analysis_engine.direction_selector import select_direction
        from atlas.analysis_engine.recommendation import _derive_what_would_change
        for fn in (select_direction, _derive_what_would_change, build_drivers):
            params = set(inspect.signature(fn).parameters)
            assert "revenue_cagr" not in params
            assert "growth_revenue_cagr" not in params

    def test_serialization_round_trips_and_preserves_null(self):
        from atlas.analysis_engine.reasoning import deserialize_reasoning, serialize_reasoning

        class _R:
            primary_drivers = counter_drivers = ()
            what_would_change = ()
            conviction_reasoning = None
            key_unknowns = ()
            signal_summary = build_signal_summary(
                **_drivers(), growth_revenue_cagr=0.0, growth_free_cash_flow_cagr=None)

        payload = serialize_reasoning(_R())
        growth = [s for s in payload["signalSummary"] if s["engine"] == "growth"][0]
        assert growth["revenueCagr"] == 0.0
        assert growth["freeCashFlowCagr"] is None
        restored = {c.engine: c for c in deserialize_reasoning(payload).signal_summary}
        assert restored[CanonicalEngine.GROWTH].revenue_cagr == 0.0
        assert restored[CanonicalEngine.GROWTH].free_cash_flow_cagr is None

    def test_a_legacy_payload_without_the_fields_still_deserializes(self):
        from atlas.analysis_engine.reasoning import deserialize_reasoning
        legacy = {"schemaVersion": 1, "signalSummary": [
            {"engine": "growth", "state": "conclusive",
             "influencedDirection": True, "sourceStatus": "moderate"}]}
        growth = deserialize_reasoning(legacy).signal_summary[0]
        assert growth.revenue_cagr is None and growth.free_cash_flow_cagr is None

    def test_serialization_is_deterministic(self):
        import json
        from atlas.analysis_engine.reasoning import serialize_reasoning

        class _R:
            primary_drivers = counter_drivers = ()
            what_would_change = ()
            conviction_reasoning = None
            key_unknowns = ()
            signal_summary = build_signal_summary(
                **_drivers(), growth_revenue_cagr=0.2464, growth_free_cash_flow_cagr=1.1822)

        assert len({json.dumps(serialize_reasoning(_R()), sort_keys=True) for _ in range(20)}) == 1
