"""Tests for `atlas.analysis_engine.recommendation_outlook_context`
(Recommendation / Decision Intelligence Sprint 1).

Scope, per the user's own binding reconciliation for this sprint: Outlook
and Recommendation stay `DE-012`/`DE-014`'s sibling conclusions.
`select_direction`/`evaluate_recommendation_gate`/
`calculate_recommendation_conviction` are untouched by this sprint --
these tests prove that structurally (signature inspection) and
empirically (an integration-level Direction-invariance test), not just by
absence of a code change. Everything else here tests the one new, small,
disclosure-only derivation this sprint adds.

Three groups:

1. `TestRelationshipRules` / `TestBoundaryAndDeterminism` /
   `TestContractValidation` -- pure unit tests of
   `derive_recommendation_outlook_context` against hand-built fixtures
   (the same "construct the type directly" style
   `test_computed_directional_recommendation.py` already established for
   this exact reason: no Direction selector detour needed to test a
   function that does not read one).
2. `TestNeverReadByGatingLogic` -- signature-level guarantees that
   `select_direction`/`calculate_recommendation_conviction`/
   `evaluate_recommendation_gate` take no Outlook-shaped parameter.
3. `TestDirectionInvariance` -- an integration-level proof, through the
   real `assemble_analysis` entry point with `build_outlook` swapped for
   two deliberately opposite canned `Outlook`s, that
   `CanonicalAnalysis.recommendation` (Direction, Conviction, reasoning)
   is identical either way, while `recommendation_outlook_context` is
   not -- Outlook changes the disclosed relationship, never the
   Recommendation itself.
4. `TestAdversarialCases` -- Part 21-style probes of the new derivation
   specifically (never of Direction selection, which this sprint does not
   touch).
"""
from __future__ import annotations

import inspect
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from atlas.analysis_engine.conviction import ConvictionAssessment, ConvictionLevel
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.outlook import (
    ExpectedReturnRange,
    HorizonOutlook,
    Outlook,
    OutlookAssumption,
    OutlookAssumptionKind,
    OutlookGapKind,
    OutlookHorizon,
    OutlookMomentumKind,
    ReturnBasis,
)
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.analysis_engine.recommendation import (
    ComputedDirectionalRecommendation,
    RecommendationAlternative,
    RecommendationConvictionLevel,
    RecommendationDirection,
    RecommendationReasoning,
    evaluate_recommendation_gate,
)
from atlas.analysis_engine.recommendation_outlook_context import (
    OutlookRecommendationRelationship,
    RecommendationOutlookContext,
    derive_recommendation_outlook_context,
)
from atlas.decision_engine.contracts import (
    RecommendationOutcomeKind,
    RecommendationWithheld,
    RecommendationWithheldReason,
)
from atlas.analysis_engine.direction_selector import select_direction
from atlas.analysis_engine.recommendation_conviction import calculate_recommendation_conviction
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_populated
from tests.unit.analysis_engine.test_outlook import _weak_growth_records


# ---------------------------------------------------------------------------
# Fixture helpers -- hand-built, deliberately minimal (mirrors
# test_computed_directional_recommendation.py's own `_valid_recommendation`
# pattern: this module reads only `recommendation`'s own type and
# `outlook`'s two `expected_return` ranges, so nothing else needs to be
# realistic).
# ---------------------------------------------------------------------------


def _withheld(reason=RecommendationWithheldReason.ENGINE_NOT_IMPLEMENTED) -> RecommendationWithheld:
    return RecommendationWithheld(
        kind=RecommendationOutcomeKind.RECOMMENDATION_WITHHELD,
        reason=reason,
        missing_evaluations=(),
        required_before_recommendation=(),
        generated_at=GENERATED_AT,
    )


def _computed(*, direction=RecommendationDirection.HOLD) -> ComputedDirectionalRecommendation:
    _, output = run_populated()
    finding = output.reasoning.finding
    factors = output.portfolio_intelligence.portfolio_factors
    assert finding is not None
    assert factors is not None
    return ComputedDirectionalRecommendation(
        recommendation_instance_id="test-instance-1",
        case_id=output.case_id,
        generated_at=GENERATED_AT,
        direction=direction,
        direction_statement="Current evidence, actively reviewed, does not support a change to this position.",
        conviction_level=RecommendationConvictionLevel.MEDIUM,
        conviction_reason="Evidence coverage is full; one open question remains unresolved.",
        reasoning=RecommendationReasoning(
            current_situation=finding.current_situation,
            supporting_evidence=finding.supporting_evidence,
            contradicting_evidence=finding.contradicting_evidence,
            portfolio_context=finding.portfolio_context,
        ),
        portfolio_factors=factors,
        alternatives=(RecommendationAlternative(label="Wait", rationale="No urgency signal present."),),
    )


def _assumption(*, growth: bool) -> OutlookAssumption:
    if growth:
        return OutlookAssumption(
            kind=OutlookAssumptionKind.HISTORICAL_GROWTH_WITH_TERMINAL_REVERSION,
            current_fcf_yield=0.04,
            target_fcf_yield=0.045,
            observation_count=6,
            growth_rate=0.08,
            horizon_years=4,
            growth_observation_count=3,
        )
    return OutlookAssumption(
        kind=OutlookAssumptionKind.HISTORICAL_FCF_YIELD_REVERSION,
        current_fcf_yield=0.04,
        target_fcf_yield=0.045,
        observation_count=6,
    )


def _range(low: float, high: float, *, growth: bool = True) -> ExpectedReturnRange:
    return ExpectedReturnRange(
        low_percent=low,
        high_percent=high,
        basis=ReturnBasis.ANNUALIZED if growth else ReturnBasis.CUMULATIVE,
        horizon_months_low=36,
        horizon_months_high=60,
        assumption=_assumption(growth=growth),
    )


def _horizon(
    *,
    expected_return: ExpectedReturnRange | None = None,
    gap: OutlookGapKind | None = None,
    horizon: OutlookHorizon = OutlookHorizon.LONG_TERM,
) -> HorizonOutlook:
    return HorizonOutlook(
        horizon=horizon,
        expected_return=expected_return,
        expected_return_gap=gap,
        scenarios=(),
        scenarios_gap=OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY,
        conviction=ConvictionLevel.MODERATE,
        momentum=OutlookMomentumKind.UNAVAILABLE,
        key_drivers=(),
    )


_ST_GAP = _horizon(gap=OutlookGapKind.NO_HISTORICAL_VALUATION_RANGE, horizon=OutlookHorizon.SHORT_TERM)


def _outlook(*, long_term: HorizonOutlook, short_term: HorizonOutlook | None = None) -> Outlook:
    return Outlook(short_term=short_term or _ST_GAP, long_term=long_term, generated_at=GENERATED_AT)


# ---------------------------------------------------------------------------
# 1. Relationship rules
# ---------------------------------------------------------------------------


class TestRelationshipRules:
    def test_withheld_recommendation_with_positive_outlook_is_unavailable(self):
        outlook = _outlook(long_term=_horizon(expected_return=_range(0.10, 0.40)))
        context = derive_recommendation_outlook_context(_withheld(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.UNAVAILABLE

    def test_withheld_recommendation_with_negative_outlook_is_unavailable(self):
        """Requirement: a withheld Recommendation never reads as
        'corroborated' just because Outlook happens to be negative too --
        there is no Recommendation to compare against."""
        outlook = _outlook(long_term=_horizon(expected_return=_range(-0.30, -0.05)))
        context = derive_recommendation_outlook_context(_withheld(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.UNAVAILABLE

    def test_entirely_negative_range_corroborates(self):
        outlook = _outlook(long_term=_horizon(expected_return=_range(-0.20, -0.05)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.CORROBORATES

    def test_entirely_positive_range_diverges(self):
        outlook = _outlook(long_term=_horizon(expected_return=_range(0.10, 0.40)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.DIVERGES

    def test_range_straddling_zero_is_mixed(self):
        outlook = _outlook(long_term=_horizon(expected_return=_range(-0.10, 0.15)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.MIXED

    def test_low_bound_exactly_zero_is_mixed_not_diverges(self):
        """Zero is the boundary, not a threshold that rounds up to
        positive -- a bear case of exactly 0% is not a guaranteed gain."""
        outlook = _outlook(long_term=_horizon(expected_return=_range(0.0, 0.20)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.MIXED

    def test_high_bound_exactly_zero_is_mixed_not_corroborates(self):
        outlook = _outlook(long_term=_horizon(expected_return=_range(-0.20, 0.0)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.MIXED

    def test_gap_expected_return_is_unavailable(self):
        outlook = _outlook(long_term=_horizon(gap=OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.UNAVAILABLE

    def test_short_term_and_long_term_computed_independently(self):
        """Never blended: Short-Term can diverge while Long-Term
        corroborates in the same call, and both are reported."""
        outlook = Outlook(
            short_term=_horizon(expected_return=_range(0.05, 0.15, growth=False), horizon=OutlookHorizon.SHORT_TERM),
            long_term=_horizon(expected_return=_range(-0.15, -0.02)),
            generated_at=GENERATED_AT,
        )
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.short_term is OutlookRecommendationRelationship.DIVERGES
        assert context.long_term is OutlookRecommendationRelationship.CORROBORATES

    def test_direction_kind_does_not_change_the_relationship(self):
        """HOLD/TRIM/NO_ACTION all structurally share 'no Valuation
        Support for Capital Deployment' -- the relationship must not
        secretly branch on which of the three it is."""
        outlook = _outlook(long_term=_horizon(expected_return=_range(-0.10, -0.01)))
        results = {
            direction: derive_recommendation_outlook_context(_computed(direction=direction), outlook).long_term
            for direction in (RecommendationDirection.HOLD, RecommendationDirection.TRIM, RecommendationDirection.NO_ACTION)
        }
        assert set(results.values()) == {OutlookRecommendationRelationship.CORROBORATES}


# ---------------------------------------------------------------------------
# 2. Determinism and contract validation
# ---------------------------------------------------------------------------


class TestBoundaryAndDeterminism:
    def test_deterministic_same_inputs_same_output(self):
        recommendation = _computed()
        outlook = _outlook(long_term=_horizon(expected_return=_range(0.02, 0.30)))
        first = derive_recommendation_outlook_context(recommendation, outlook)
        second = derive_recommendation_outlook_context(recommendation, outlook)
        assert first == second

    def test_result_is_always_the_dataclass_type(self):
        outlook = _outlook(long_term=_horizon(expected_return=_range(0.02, 0.30)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert isinstance(context, RecommendationOutlookContext)


class TestContractValidation:
    def test_rejects_non_enum_short_term(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationOutlookContext(
                short_term="corroborates",  # a bare string, not the enum
                long_term=OutlookRecommendationRelationship.MIXED,
            )

    def test_rejects_non_enum_long_term(self):
        with pytest.raises(AnalysisEngineContractError):
            RecommendationOutlookContext(
                short_term=OutlookRecommendationRelationship.MIXED,
                long_term="diverges",
            )

    def test_exactly_four_relationship_members(self):
        assert {m.value for m in OutlookRecommendationRelationship} == {
            "corroborates",
            "diverges",
            "mixed",
            "unavailable",
        }


# ---------------------------------------------------------------------------
# 3. Never read by gating logic -- structural guarantee, not just absence
#    of a code change.
# ---------------------------------------------------------------------------


class TestNeverReadByGatingLogic:
    def test_select_direction_has_no_outlook_parameter(self):
        params = inspect.signature(select_direction).parameters
        assert not any("outlook" in name for name in params)

    def test_calculate_recommendation_conviction_has_no_outlook_parameter(self):
        params = inspect.signature(calculate_recommendation_conviction).parameters
        assert not any("outlook" in name for name in params)

    def test_evaluate_recommendation_gate_has_no_outlook_parameter(self):
        params = inspect.signature(evaluate_recommendation_gate).parameters
        assert not any("outlook" in name for name in params)

    def test_derive_function_only_takes_recommendation_and_outlook(self):
        """The derivation itself takes no Business/Valuation/Portfolio/
        Reasoning input -- it reads only the two already-computed,
        already-final conclusions, never re-derives anything upstream."""
        params = list(inspect.signature(derive_recommendation_outlook_context).parameters)
        assert params == ["recommendation", "outlook"]


# ---------------------------------------------------------------------------
# 4. Direction invariance -- integration-level proof through the real
#    pipeline entry point.
# ---------------------------------------------------------------------------


def _real_computed_direction_fixture():
    """A real, non-withheld `ComputedDirectionalRecommendation`, reached
    through the actual pipeline end to end -- a held position (`ACME`,
    via `PortfolioHoldingContext`) with genuinely declining Revenue and
    Free Cash Flow (`_weak_growth_records`, already used and verified in
    `test_outlook.py`), which `select_direction`'s own stage 4 makes
    real, case-specific negative evidence sufficient for TRIM by itself,
    independent of Valuation. `run_populated()`'s own default fixture
    never reaches a real Direction (all four adopted stages don't clear
    the hard gate together), so this dedicated fixture is required for
    a meaningful Direction-invariance test."""
    import dataclasses as dc

    from atlas.decision_engine.contracts import PortfolioHoldingContext
    from atlas.decision_engine.pipeline import run_pipeline
    from tests.unit.decision_engine._fixtures import build_populated_input

    base_input = build_populated_input(case_id="direction-invariance-case")
    engine_input = dc.replace(
        base_input, portfolio_holding=PortfolioHoldingContext(ticker="ACME", weight_percent=4.0)
    )
    decision_output = run_pipeline(engine_input, generated_at=GENERATED_AT)
    return engine_input, decision_output, _weak_growth_records()


class TestDirectionInvariance:
    def test_recommendation_is_byte_identical_regardless_of_outlook_content(self):
        """Swap `build_outlook`'s return value for two deliberately
        opposite canned `Outlook`s (strongly positive vs strongly
        negative Long-Term Expected Return) while holding every other
        `assemble_analysis` input identical. `CanonicalAnalysis
        .recommendation` (Direction, Conviction, reasoning) must be
        identical either way; only `recommendation_outlook_context` may
        differ."""
        engine_input, decision_output, records = _real_computed_direction_fixture()

        positive_outlook = _outlook(long_term=_horizon(expected_return=_range(0.15, 0.45)))
        negative_outlook = _outlook(long_term=_horizon(expected_return=_range(-0.30, -0.10)))

        with patch("atlas.analysis_engine.pipeline.build_outlook", return_value=positive_outlook):
            analysis_positive = assemble_analysis(
                engine_input, decision_output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
            )
        with patch("atlas.analysis_engine.pipeline.build_outlook", return_value=negative_outlook):
            analysis_negative = assemble_analysis(
                engine_input, decision_output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
            )

        # First confirm this fixture actually reaches a real, non-withheld
        # Direction -- otherwise the assertions below would pass
        # vacuously (both sides UNAVAILABLE/RecommendationWithheld) and
        # prove nothing.
        assert isinstance(analysis_positive.recommendation.recommendation, ComputedDirectionalRecommendation)
        assert analysis_positive.recommendation.recommendation.direction is RecommendationDirection.TRIM

        assert analysis_positive.recommendation == analysis_negative.recommendation
        assert analysis_positive.conviction == analysis_negative.conviction
        # The one field that IS allowed, and expected, to differ.
        assert analysis_positive.recommendation_outlook_context != analysis_negative.recommendation_outlook_context
        assert analysis_positive.recommendation_outlook_context.long_term is OutlookRecommendationRelationship.DIVERGES
        assert analysis_negative.recommendation_outlook_context.long_term is OutlookRecommendationRelationship.CORROBORATES

    def test_pipeline_wiring_matches_the_pure_function_for_a_real_run(self):
        """Consistency check: `pipeline.py`'s own call site must produce
        exactly what `derive_recommendation_outlook_context` would
        produce for the same two already-computed objects -- no drift
        between the wiring and the function it wires."""
        engine_input, decision_output = run_populated()
        analysis = assemble_analysis(engine_input, decision_output, is_thesis_stale=False, generated_at=GENERATED_AT)
        expected = derive_recommendation_outlook_context(analysis.recommendation.recommendation, analysis.outlook)
        assert analysis.recommendation_outlook_context == expected


# ---------------------------------------------------------------------------
# 5. Adversarial cases (Part 21), scoped to the new derivation only.
# ---------------------------------------------------------------------------


class TestAdversarialCases:
    def test_both_horizons_unavailable_when_outlook_itself_fully_gapped(self):
        outlook = Outlook(
            short_term=_horizon(gap=OutlookGapKind.VALUATION_NOT_CONCLUSIVE, horizon=OutlookHorizon.SHORT_TERM),
            long_term=_horizon(gap=OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY),
            generated_at=GENERATED_AT,
        )
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.short_term is OutlookRecommendationRelationship.UNAVAILABLE
        assert context.long_term is OutlookRecommendationRelationship.UNAVAILABLE

    def test_function_never_reads_outlook_generated_at_for_staleness(self):
        """No staleness comparison is invented: an Outlook computed at a
        completely different wall-clock time from the Recommendation
        still yields a real relationship, never a fabricated
        'unavailable due to staleness' -- this codebase's own recency
        judgments live elsewhere (Change Intelligence), not here."""
        stale_outlook = Outlook(
            short_term=_ST_GAP,
            long_term=_horizon(expected_return=_range(-0.10, -0.01)),
            generated_at=datetime(2001, 1, 1, tzinfo=timezone.utc),
        )
        context = derive_recommendation_outlook_context(_computed(), stale_outlook)
        assert context.long_term is OutlookRecommendationRelationship.CORROBORATES

    def test_function_never_reads_scenarios_momentum_or_conviction(self):
        """Explicit negative check for the reconciliation's own forbidden
        -input list, applied to this sibling module (not
        select_direction/gating, which never receive these at all): the
        relationship must be driven by `expected_return`'s sign alone,
        even when scenarios/momentum/conviction are deliberately set to
        values that would suggest the opposite conclusion if they were
        (wrongly) being read."""
        misleading_horizon = HorizonOutlook(
            horizon=OutlookHorizon.LONG_TERM,
            expected_return=_range(-0.20, -0.05),  # negative -> should corroborate
            expected_return_gap=None,
            scenarios=(),
            scenarios_gap=OutlookGapKind.NO_DURABLE_GROWTH_TRAJECTORY,
            conviction=ConvictionLevel.VERY_HIGH,  # would suggest "trust this a lot" if read
            momentum=OutlookMomentumKind.STRENGTHENING,  # would suggest positive if read
            key_drivers=(),
        )
        outlook = _outlook(long_term=misleading_horizon)
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.CORROBORATES

    def test_recommendation_withheld_reason_does_not_matter(self):
        """Every RecommendationWithheldReason collapses to the same
        UNAVAILABLE outcome -- the relationship is about whether a
        Direction exists at all, never why it doesn't."""
        outlook = _outlook(long_term=_horizon(expected_return=_range(-0.10, -0.01)))
        for reason in RecommendationWithheldReason:
            context = derive_recommendation_outlook_context(_withheld(reason=reason), outlook)
            assert context.long_term is OutlookRecommendationRelationship.UNAVAILABLE

    def test_extremely_wide_range_still_classified_by_sign_alone(self):
        """No magnitude threshold anywhere -- an enormous range is
        classified identically to a narrow one, as long as the sign
        pattern matches."""
        outlook = _outlook(long_term=_horizon(expected_return=_range(-5.0, -0.001)))
        context = derive_recommendation_outlook_context(_computed(), outlook)
        assert context.long_term is OutlookRecommendationRelationship.CORROBORATES
