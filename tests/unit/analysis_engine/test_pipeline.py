"""Tests for `atlas.analysis_engine.pipeline.assemble_analysis`
(ATLAS-020 Phase 2/3) -- structural completeness, determinism, and the
sprint's own hard constraints (no fabricated recommendation, no
numeric conviction, Catalysts/Scenario Analysis honestly absent)."""
from __future__ import annotations

import dataclasses

from atlas.analysis_engine.contracts import CapabilityStatus
from atlas.analysis_engine.conviction import ConvictionLevel
from atlas.analysis_engine.findings import FindingKind
from atlas.analysis_engine.models import UnavailableCapability
from atlas.analysis_engine.pipeline import assemble_analysis
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import DecisionEngineInput, RecommendationOutcomeKind
from atlas.decision_engine.pipeline import run_pipeline
from tests.unit.analysis_engine._fixtures import (
    EVALUATED_AT,
    GENERATED_AT,
    build_evidence,
    build_observation,
    run_minimal,
    run_populated,
)


class TestStructuralCompleteness:
    def test_every_section_is_present_for_minimal_input(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.identity.case_id == str(engine_input.case_id)
        assert analysis.business is output.business_evaluation
        assert analysis.valuation is output.valuation
        assert analysis.portfolio_intelligence is output.portfolio_intelligence
        assert analysis.reasoning is output.reasoning
        assert analysis.confidence is output.business_evaluation.evidence_quality.coverage
        assert analysis.risk is not None
        assert analysis.conviction is not None
        assert analysis.recommendation is not None
        assert analysis.findings
        assert analysis.business_analysis is not None
        assert analysis.generated_at == GENERATED_AT

    def test_reused_stage_results_are_the_same_objects_not_copies(self):
        """Phase 2's "do not duplicate existing logic" -- proven at the
        object-identity level, not just equality."""
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.business is output.business_evaluation
        assert analysis.valuation is output.valuation
        assert analysis.portfolio_intelligence is output.portfolio_intelligence
        assert analysis.reasoning is output.reasoning


class TestCatalystsAndScenarioAnalysisAreHonestlyAbsent:
    def test_both_are_unavailable_capability_markers(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.catalysts == UnavailableCapability(reason=CapabilityStatus.NOT_YET_IMPLEMENTED)
        assert analysis.scenario_analysis == UnavailableCapability(
            reason=CapabilityStatus.NOT_YET_IMPLEMENTED
        )


class TestBusinessAnalysisIntegration:
    """ATLAS-021: `CanonicalAnalysis.business_analysis` and its flat
    `BUSINESS_CATEGORY_ASSESSED` projection into `analysis.findings`."""

    def test_business_analysis_has_all_six_categories(self):
        from atlas.analysis_engine.business import BusinessCategory

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert {f.kind for f in analysis.business_analysis.findings} == set(BusinessCategory)

    def test_six_business_category_assessed_findings_appear_in_the_flat_list(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        matches = [f for f in analysis.findings if f.kind is FindingKind.BUSINESS_CATEGORY_ASSESSED]
        assert len(matches) == 6

    def test_projected_findings_carry_category_and_status_in_details(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        matches = [f for f in analysis.findings if f.kind is FindingKind.BUSINESS_CATEGORY_ASSESSED]
        categories = {f.details["category"] for f in matches}
        assert categories == {
            "business_model",
            "competitive_position",
            "management",
            "capital_allocation",
            "growth",
            "durability",
        }
        assert all(f.details["status"] == "insufficient_input" for f in matches)

    def test_business_category_findings_do_not_leak_into_risk_section(self):
        """business_category_assessed Findings carry no `risk_category`
        key -- they must never be picked up by the risk-section filter,
        which only matches on that key's presence."""
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        risk_ids = {f.id for f in analysis.risk.findings}
        business_ids = {
            f.id for f in analysis.findings if f.kind is FindingKind.BUSINESS_CATEGORY_ASSESSED
        }
        assert risk_ids.isdisjoint(business_ids)

    def test_existing_business_analysis_unavailable_finding_is_unaffected(self):
        """Backward compatibility: the pre-existing decision_engine-level
        BUSINESS_ANALYSIS_UNAVAILABLE finding (ATLAS-020) still appears
        exactly once, unchanged, alongside the six new ones."""
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        matches = [f for f in analysis.findings if f.kind is FindingKind.BUSINESS_ANALYSIS_UNAVAILABLE]
        assert len(matches) == 1

    def test_no_duplicated_durability_computation(self):
        """The Durability BusinessFinding's status must match
        decision_engine's own Durability conclusion exactly -- proving
        reuse, not an independent second computation that could drift."""
        from atlas.analysis_engine.business import BusinessCategory, BusinessCategoryStatus
        from atlas.decision_engine.contracts import EvaluationState as DEState

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        durability_finding = next(
            f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.DURABILITY
        )
        assert output.business_evaluation.durability.state is DEState.INSUFFICIENT_INPUT
        assert durability_finding.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_conviction_and_recommendation_behavior_is_unchanged_by_business_analysis(self):
        """ATLAS-021 must not alter Conviction or Recommendation Gate
        behavior -- both are computed from the same signals as before,
        untouched by the new business_analysis field."""
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.conviction.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert (
            analysis.recommendation.recommendation.kind
            is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        )

    def test_determinism_holds_with_business_analysis_included(self):
        engine_input, output = run_populated()
        first = assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        second = assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        assert first.business_analysis == second.business_analysis
        assert first == second


class TestNoFabrication:
    def test_recommendation_is_always_withheld(self):
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert (
            analysis.recommendation.recommendation.kind
            is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD
        )

    def test_no_directional_recommendation_type_exists_anywhere(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert not hasattr(analysis.recommendation, "direction")
        assert not hasattr(analysis, "direction")

    def test_conviction_level_is_categorical_not_numeric(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert isinstance(analysis.conviction.level, ConvictionLevel)
        assert not hasattr(analysis.conviction, "score")

    def test_very_high_conviction_is_unreachable_with_todays_evaluators(self):
        """`assemble_analysis` never passes `business_conclusive=True`/
        `valuation_conclusive=True` -- both are structurally impossible
        to compute today (Durability/substantive Valuation are always
        `INSUFFICIENT_INPUT`) -- so `VERY_HIGH` must never appear from a
        real pipeline run, no matter the input."""
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.conviction.level is not ConvictionLevel.VERY_HIGH


class TestFindingsAssembly:
    def test_every_finding_kind_used_is_a_real_enum_member(self):
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        for finding in analysis.findings:
            assert isinstance(finding.kind, FindingKind)

    def test_finding_ids_are_unique(self):
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        ids = [finding.id for finding in analysis.findings]
        assert len(ids) == len(set(ids))

    def test_conviction_assessed_finding_reflects_the_real_conviction_level(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        conviction_findings = [
            f for f in analysis.findings if f.kind is FindingKind.CONVICTION_ASSESSED
        ]
        assert len(conviction_findings) == 1
        assert conviction_findings[0].details["level"] == analysis.conviction.level.value

    def test_recommendation_withheld_finding_present_exactly_once(self):
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        matches = [f for f in analysis.findings if f.kind is FindingKind.RECOMMENDATION_WITHHELD]
        assert len(matches) == 1
        assert matches[0].details["conviction_gate_met"] == analysis.recommendation.conviction_gate_met

    def test_seven_portfolio_factor_unavailable_findings_for_minimal_input(self):
        """`PortfolioFinding.factors` always names all seven `DE-003`
        factors -- proven here at the Findings level too."""
        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        matches = [
            f for f in analysis.findings if f.kind is FindingKind.PORTFOLIO_FACTOR_UNAVAILABLE
        ]
        assert len(matches) == 7


class TestRiskSection:
    def test_no_risk_findings_when_there_is_no_contradicting_evidence(self):
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.risk.findings == ()

    def test_thesis_risk_finding_appears_when_evidence_contradicts_an_observation(self):
        case_id = CaseId()
        observation = build_observation(case_id=case_id)
        challenging = build_evidence(observation=observation, direction=Direction.CHALLENGES)
        engine_input = DecisionEngineInput(
            case_id=case_id,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(challenging,),
        )
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert len(analysis.risk.findings) == 1
        risk_finding = analysis.risk.findings[0]
        assert risk_finding.details["risk_category"] == "thesis_risk"
        assert risk_finding in analysis.findings

    def test_risk_findings_are_always_a_subset_of_the_top_level_findings(self):
        case_id = CaseId()
        observation = build_observation(case_id=case_id)
        challenging = build_evidence(observation=observation, direction=Direction.CHALLENGES)
        engine_input = DecisionEngineInput(
            case_id=case_id,
            evaluated_at=EVALUATED_AT,
            observations=(observation,),
            evidence=(challenging,),
        )
        output = run_pipeline(engine_input, generated_at=GENERATED_AT)
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        top_level_ids = {finding.id for finding in analysis.findings}
        assert {finding.id for finding in analysis.risk.findings}.issubset(top_level_ids)


class TestThesisStalenessFeedsConviction:
    def test_stale_thesis_caps_conviction_at_moderate_even_with_full_coverage(self):
        engine_input, output = run_populated()
        fresh = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        stale = assemble_analysis(
            engine_input, output, is_thesis_stale=True, generated_at=GENERATED_AT
        )
        if fresh.conviction.level is ConvictionLevel.HIGH:
            assert stale.conviction.level is ConvictionLevel.MODERATE


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_analysis(self):
        engine_input, output = run_populated()
        first = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        second = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert first == second

    def test_engine_input_is_not_mutated(self):
        engine_input, output = run_populated()
        before = dataclasses.replace(engine_input)
        assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        assert engine_input == before
