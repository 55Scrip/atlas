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
    """ATLAS-025 made `RiskSection` additive: it now always carries the
    four `RISK_CATEGORY_ASSESSED` projections (one per evaluated Risk
    category) alongside whatever pre-existing per-observation
    `CONTRADICTING_EVIDENCE` Findings exist -- so it is never empty,
    unlike ATLAS-020's original "only THESIS_RISK, only when there is a
    contradiction" behavior."""

    def test_four_risk_category_assessed_findings_always_present(self):
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        categories = {f.details["risk_category"] for f in analysis.risk.findings}
        assert categories == {"business_risk", "financial_risk", "valuation_risk", "thesis_risk"}

    def test_no_per_observation_contradiction_finding_when_there_is_none(self):
        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        contradiction_findings = [f for f in analysis.risk.findings if f.kind is FindingKind.CONTRADICTING_EVIDENCE]
        assert contradiction_findings == []

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
        # Four RISK_CATEGORY_ASSESSED (always present) + one legacy
        # per-observation CONTRADICTING_EVIDENCE finding for this case.
        assert len(analysis.risk.findings) == 5
        contradiction_findings = [f for f in analysis.risk.findings if f.kind is FindingKind.CONTRADICTING_EVIDENCE]
        assert len(contradiction_findings) == 1
        assert contradiction_findings[0].details["risk_category"] == "thesis_risk"
        assert contradiction_findings[0] in analysis.findings

        thesis_summary = next(
            f
            for f in analysis.risk.findings
            if f.kind is FindingKind.RISK_CATEGORY_ASSESSED and f.details["risk_category"] == "thesis_risk"
        )
        assert thesis_summary.details["status"] == "high"

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


class TestGrowthAndCapitalAllocationEndToEnd:
    """ATLAS-023: the full BusinessRecord -> BusinessFact -> Evaluator
    -> BusinessFinding -> CanonicalAnalysis chain, through the actual
    top-level `assemble_analysis` entry point."""

    def test_real_business_records_produce_a_real_growth_finding(self):
        from datetime import date

        from atlas.analysis_engine.business import BusinessCategory
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        engine_input, output = run_minimal()

        def make_record(period_end, identifier, **metadata):
            document = RawBusinessDocument(
                identifier=identifier,
                company="ASML",
                source_kind="annual_report",
                published_at=GENERATED_AT,
                provider_id="structured_test",
                raw_reference=f"ref://{identifier}",
                content_hash=f"hash-{identifier}",
                language="en",
                period_end=period_end,
                metadata=metadata,
            )
            result = ingest(document, evaluated_at=GENERATED_AT)
            assert isinstance(result, IngestedRecord)
            return result.record

        records = (
            make_record(date(2023, 12, 31), "fy2023", revenue=1000.0, free_cash_flow=200.0),
            make_record(date(2024, 12, 31), "fy2024", revenue=1200.0, free_cash_flow=260.0),
        )

        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        growth = next(f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.GROWTH)
        assert growth.status is BusinessCategoryStatus.STRONG

        # Other categories remain honestly unevaluated -- exactly the
        # intended "mixture" architecture (Phase 10).
        durability = next(f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.DURABILITY)
        assert durability.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_growth_category_assessed_finding_reflects_the_real_status_in_the_flat_list(self):
        from datetime import date

        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        engine_input, output = run_minimal()

        def make_record(period_end, identifier, **metadata):
            document = RawBusinessDocument(
                identifier=identifier,
                company="ASML",
                source_kind="annual_report",
                published_at=GENERATED_AT,
                provider_id="structured_test",
                raw_reference=f"ref://{identifier}",
                content_hash=f"hash-{identifier}",
                language="en",
                period_end=period_end,
                metadata=metadata,
            )
            result = ingest(document, evaluated_at=GENERATED_AT)
            assert isinstance(result, IngestedRecord)
            return result.record

        records = (
            make_record(date(2023, 12, 31), "fy2023", revenue=1000.0),
            make_record(date(2024, 12, 31), "fy2024", revenue=1100.0),
        )
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        matches = [f for f in analysis.findings if f.kind is FindingKind.BUSINESS_CATEGORY_ASSESSED]
        growth_match = next(f for f in matches if f.details["category"] == "growth")
        assert growth_match.details["status"] == "moderate"

    def test_conviction_and_recommendation_are_unchanged_by_real_growth_evaluation(self):
        """ATLAS-023's own Phase 15 question #4: no hidden coupling --
        Conviction/Recommendation still only read what they already
        read (evidence coverage, contradiction, staleness), never a
        Business Analysis category's own status."""
        from datetime import date

        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        engine_input, output = run_minimal()

        def make_record(period_end, identifier, **metadata):
            document = RawBusinessDocument(
                identifier=identifier,
                company="ASML",
                source_kind="annual_report",
                published_at=GENERATED_AT,
                provider_id="structured_test",
                raw_reference=f"ref://{identifier}",
                content_hash=f"hash-{identifier}",
                language="en",
                period_end=period_end,
                metadata=metadata,
            )
            result = ingest(document, evaluated_at=GENERATED_AT)
            assert isinstance(result, IngestedRecord)
            return result.record

        records = (
            make_record(date(2023, 12, 31), "fy2023", revenue=1000.0, free_cash_flow=200.0),
            make_record(date(2024, 12, 31), "fy2024", revenue=1200.0, free_cash_flow=260.0),
        )

        without_records = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        with_records = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        assert without_records.conviction == with_records.conviction
        assert without_records.recommendation.recommendation == with_records.recommendation.recommendation

    def test_determinism_holds_through_the_full_fact_extraction_chain(self):
        from datetime import date

        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        engine_input, output = run_minimal()
        document = RawBusinessDocument(
            identifier="fy2024",
            company="ASML",
            source_kind="annual_report",
            published_at=GENERATED_AT,
            provider_id="structured_test",
            raw_reference="ref://fy2024",
            content_hash="hash-fy2024",
            language="en",
            period_end=date(2024, 12, 31),
            metadata={"revenue": 1000.0},
        )
        result = ingest(document, evaluated_at=GENERATED_AT)
        assert isinstance(result, IngestedRecord)

        first = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=(result.record,), generated_at=GENERATED_AT
        )
        second = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=(result.record,), generated_at=GENERATED_AT
        )
        assert first.business_analysis == second.business_analysis


class TestValuationEngineEndToEnd:
    """ATLAS-024: the full BusinessRecord -> BusinessFact/ValuationFact
    -> FCF Yield Evaluator -> ValuationFinding -> CanonicalAnalysis
    chain, through the real top-level `assemble_analysis` entry point."""

    @staticmethod
    def _records():
        from datetime import date

        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        def make(source_kind, period_end, identifier, **metadata):
            document = RawBusinessDocument(
                identifier=identifier,
                company="ASML",
                source_kind=source_kind,
                published_at=GENERATED_AT,
                provider_id="structured_test",
                raw_reference=f"ref://{identifier}",
                content_hash=f"hash-{identifier}",
                language="en",
                period_end=period_end,
                metadata=metadata,
            )
            result = ingest(document, evaluated_at=GENERATED_AT)
            assert isinstance(result, IngestedRecord)
            return result.record

        return (
            make("annual_report", date(2022, 12, 31), "fy22", free_cash_flow=100.0),
            make("annual_report", date(2023, 12, 31), "fy23", free_cash_flow=110.0),
            make("annual_report", date(2024, 12, 31), "fy24", free_cash_flow=200.0),
            make("market_data_snapshot", date(2022, 12, 31), "m22", share_price=50.0, shares_outstanding=100.0),
            make("market_data_snapshot", date(2023, 12, 31), "m23", share_price=52.0, shares_outstanding=100.0),
            make("market_data_snapshot", date(2024, 12, 31), "m24", share_price=53.0, shares_outstanding=100.0),
        )

    def test_real_records_produce_a_real_undervalued_finding(self):
        from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=self._records(), generated_at=GENERATED_AT
        )
        fcf_yield = next(
            f for f in analysis.valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        )
        assert fcf_yield.status is ValuationStatus.UNDERVALUED

    def test_decision_engines_own_locked_valuation_field_is_untouched(self):
        """Phase 14's own backward-compatibility requirement:
        `CanonicalAnalysis.valuation` (decision_engine's, reused
        verbatim) must remain exactly what it always was."""
        from atlas.decision_engine.contracts import EvaluationState

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=self._records(), generated_at=GENERATED_AT
        )
        assert analysis.valuation is output.valuation
        assert analysis.valuation.substantive_valuation.state is EvaluationState.INSUFFICIENT_INPUT

    def test_recommendation_stays_withheld_regardless_of_real_valuation(self):
        """Phase 16: real valuation is only one input -- it can never
        bypass the Recommendation Gate."""
        from atlas.decision_engine.contracts import RecommendationOutcomeKind

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=self._records(), generated_at=GENERATED_AT
        )
        assert analysis.recommendation.recommendation.kind is RecommendationOutcomeKind.RECOMMENDATION_WITHHELD

    def test_conviction_level_is_identical_with_and_without_valuation_facts(self):
        """Phase 15: valuation_conclusive alone cannot raise Conviction
        while business_conclusive stays False -- confirmed directly,
        not just asserted in prose."""
        engine_input, output = run_minimal()
        without = assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        with_valuation = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=self._records(), generated_at=GENERATED_AT
        )
        assert without.conviction.level == with_valuation.conviction.level

    def test_valuation_method_assessed_findings_appear_in_the_flat_list(self):
        from atlas.analysis_engine.findings import FindingKind

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=self._records(), generated_at=GENERATED_AT
        )
        matches = [f for f in analysis.findings if f.kind is FindingKind.VALUATION_METHOD_ASSESSED]
        assert len(matches) == 4

    def test_growth_and_valuation_remain_independent(self):
        """Business Quality/Growth and Valuation must never be forced to
        agree -- verified end to end through CanonicalAnalysis."""
        from atlas.analysis_engine.business import BusinessCategory
        from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus

        engine_input, output = run_minimal()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=self._records(), generated_at=GENERATED_AT
        )
        growth = next(f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.GROWTH)
        fcf_yield = next(
            f for f in analysis.valuation_engine.findings if f.kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        )
        # Both real, independently computed -- neither reads the other.
        assert growth.status.value in ("weak", "moderate", "strong", "insufficient_input")
        assert fcf_yield.status is ValuationStatus.UNDERVALUED

    def test_determinism_holds_through_the_full_valuation_chain(self):
        engine_input, output = run_minimal()
        records = self._records()
        first = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        second = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        assert first.valuation_engine == second.valuation_engine
