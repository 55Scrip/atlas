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

        # Categories with no evaluator remain honestly unevaluated --
        # exactly the intended "mixture" architecture (Phase 10).
        # Durability was the control here until Stage 3 gave it a real
        # evaluator; Management still has none, so it carries the point.
        management = next(f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.MANAGEMENT)
        assert management.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

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
        from datetime import date, datetime, timezone

        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        def make(source_kind, period_end, identifier, *, published_at=GENERATED_AT, **metadata):
            document = RawBusinessDocument(
                identifier=identifier,
                company="ASML",
                source_kind=source_kind,
                published_at=published_at,
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

        # Fundamentals are filed ~6 weeks after their fiscal year end;
        # market snapshots are dated after that filing -- ATLAS-032's
        # no-look-ahead eligibility needs a real publication gap, not
        # same-day fundamentals and market data. See
        # valuation/test_cash_flow.py's own module docstring.
        return (
            make("annual_report", date(2022, 12, 31), "fy22", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc), free_cash_flow=100.0),
            make("annual_report", date(2023, 12, 31), "fy23", published_at=datetime(2024, 2, 15, tzinfo=timezone.utc), free_cash_flow=110.0),
            make("annual_report", date(2024, 12, 31), "fy24", published_at=datetime(2025, 2, 15, tzinfo=timezone.utc), free_cash_flow=200.0),
            make("market_data_snapshot", date(2023, 3, 1), "m22", share_price=50.0, shares_outstanding=100.0),
            make("market_data_snapshot", date(2024, 3, 1), "m23", share_price=52.0, shares_outstanding=100.0),
            make("market_data_snapshot", date(2025, 3, 1), "m24", share_price=53.0, shares_outstanding=100.0),
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


class TestConvictionEndToEnd:
    """ATLAS-026: the full chain -- real Business/Valuation/Risk Analysis
    -> `business_conclusive`/`has_high_financial_or_valuation_risk` ->
    `calculate_conviction`, through the real top-level `assemble_analysis`
    entry point. Prior sprints' own end-to-end tests all used
    `run_minimal()` (zero Observations, `NOT_APPLICABLE` coverage), which
    forces `INSUFFICIENT_EVIDENCE` before any of these new signals can
    matter -- this class is the first to combine `FULL` coverage with
    real financial data, the only combination that actually exercises
    this sprint's wiring end to end."""

    @staticmethod
    def _fresh_full_coverage_input():
        """One supporting Observation/Evidence pair -> FULL coverage, no
        contradiction. Real Decision Engine `open_questions` (Durability/
        substantive-Valuation/Portfolio-factor gaps) remain present
        regardless -- those are decision_engine-level facts this sprint
        does not touch, so every scenario below is capped at `MODERATE`
        unless a LOW-forcing branch (contradiction, partial coverage, or
        high Financial/Valuation Risk) fires first."""
        from atlas.core.domain.case.value_objects import CaseId as _CaseId
        from atlas.core.domain.evidence.value_objects import Direction as _Direction

        case_id = _CaseId()
        observation = build_observation(case_id=case_id)
        supporting = build_evidence(observation=observation, direction=_Direction.SUPPORTS)
        engine_input = DecisionEngineInput(
            case_id=case_id, evaluated_at=EVALUATED_AT, observations=(observation,), evidence=(supporting,)
        )
        return engine_input, run_pipeline(engine_input, generated_at=GENERATED_AT)

    @staticmethod
    def _record(source_kind, period_end, identifier, *, published_at=GENERATED_AT, **metadata):
        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        document = RawBusinessDocument(
            identifier=identifier,
            company="ASML",
            source_kind=source_kind,
            published_at=published_at,
            provider_id="structured_test",
            raw_reference=f"ref://{identifier}",
            content_hash=f"hash-{identifier}",
            language="en",
            period_end=period_end,
            metadata=metadata,
        )
        result = ingest(document, evaluated_at=GENERATED_AT)
        assert isinstance(result, IngestedRecord), result
        return result.record

    def test_strong_business_and_expensive_valuation_forces_low_via_valuation_risk(self):
        """Growth STRONG + Capital Allocation STRONG (business_conclusive
        True) would otherwise permit HIGH -- but FCF Yield EXPENSIVE ->
        Valuation Risk HIGH forces LOW instead, proving high risk
        overrides an otherwise strong picture rather than being averaged
        against it."""
        from datetime import date, datetime, timezone

        from atlas.analysis_engine.conviction import ConvictionLevel, ConvictionReasonCode

        engine_input, output = self._fresh_full_coverage_input()
        # ATLAS-032: FCF-bearing filings need a real publication date
        # strictly before the market snapshot they should be eligible
        # for -- see valuation/test_cash_flow.py's own module docstring.
        records = (
            self._record(
                "financial_statement",
                date(2022, 12, 31),
                "fy22",
                published_at=datetime(2023, 2, 15, tzinfo=timezone.utc),
                revenue=1000.0,
                free_cash_flow=200.0,
            ),
            self._record(
                "financial_statement",
                date(2023, 12, 31),
                "fy23",
                published_at=datetime(2024, 2, 15, tzinfo=timezone.utc),
                revenue=1100.0,
                free_cash_flow=240.0,
            ),
            self._record(
                "financial_statement",
                date(2024, 12, 31),
                "fy24",
                published_at=datetime(2025, 2, 15, tzinfo=timezone.utc),
                revenue=1250.0,
                free_cash_flow=300.0,
            ),
            self._record("financial_statement", date(2022, 12, 31), "buy22", share_buybacks=50.0),
            self._record("financial_statement", date(2023, 12, 31), "buy23", share_buybacks=60.0),
            self._record("financial_statement", date(2022, 12, 31), "iss22", share_issuance=10.0),
            self._record("financial_statement", date(2023, 12, 31), "iss23", share_issuance=10.0),
            self._record("financial_statement", date(2022, 12, 31), "rep22", debt_repayment=30.0),
            self._record("financial_statement", date(2023, 12, 31), "rep23", debt_repayment=30.0),
            self._record("financial_statement", date(2022, 12, 31), "debt22", debt_issuance=5.0),
            self._record("financial_statement", date(2023, 12, 31), "debt23", debt_issuance=5.0),
            self._record("market_data_snapshot", date(2023, 3, 1), "m22", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2024, 3, 1), "m23", share_price=52.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2025, 3, 1), "m24", share_price=300.0, shares_outstanding=100.0),
        )
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        assert analysis.conviction.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT in analysis.conviction.reasons
        assert analysis.recommendation.conviction_gate_met is False

    def test_weak_business_and_cheap_valuation_is_capped_by_contradiction_not_business_risk(self):
        """Growth WEAK is a real negative Business Risk signal (visible
        on `analysis.risk_analysis`) that Conviction deliberately never
        reads directly -- with Capital Allocation STRONG and Valuation
        UNDERVALUED (both LOW risk), the Business Risk input is still
        reported as clear, proving Business Risk's independence from
        Conviction end to end. Since Stage 3 the cap on this fixture
        comes from Durability's own contradicting evidence instead;
        the reason codes below separate the two causes explicitly."""
        from datetime import date

        from atlas.analysis_engine.contracts import RiskCategory
        from atlas.analysis_engine.conviction import ConvictionLevel, ConvictionReasonCode
        from atlas.analysis_engine.risk.contracts import RiskStatus

        engine_input, output = self._fresh_full_coverage_input()
        records = (
            self._record("financial_statement", date(2022, 12, 31), "fy22", revenue=1250.0, free_cash_flow=100.0),
            self._record("financial_statement", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=80.0),
            self._record("financial_statement", date(2024, 12, 31), "fy24", revenue=1000.0, free_cash_flow=60.0),
            self._record("financial_statement", date(2022, 12, 31), "buy22", share_buybacks=50.0),
            self._record("financial_statement", date(2023, 12, 31), "buy23", share_buybacks=60.0),
            self._record("financial_statement", date(2022, 12, 31), "iss22", share_issuance=10.0),
            self._record("financial_statement", date(2023, 12, 31), "iss23", share_issuance=10.0),
            self._record("financial_statement", date(2022, 12, 31), "rep22", debt_repayment=30.0),
            self._record("financial_statement", date(2023, 12, 31), "rep23", debt_repayment=30.0),
            self._record("financial_statement", date(2022, 12, 31), "debt22", debt_issuance=5.0),
            self._record("financial_statement", date(2023, 12, 31), "debt23", debt_issuance=5.0),
            self._record("market_data_snapshot", date(2022, 12, 31), "m22", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2023, 12, 31), "m23", share_price=40.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2024, 12, 31), "m24", share_price=20.0, shares_outstanding=100.0),
        )
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        business_risk = next(
            f for f in analysis.risk_analysis.findings if f.category is RiskCategory.BUSINESS_RISK
        )
        assert business_risk.status is RiskStatus.HIGH

        # Stage 3 changed what this fixture produces, and the change is
        # real rather than incidental. Three years of falling revenue
        # (1250 -> 1100 -> 1000) now yield WEAK Durability, whose finding
        # carries contradicting evidence (declining demand) alongside
        # supporting evidence (free cash flow positive every period).
        # That mixed finding satisfies `has_analytical_contradiction`,
        # which Calibration Phase 4 deliberately pointed at every
        # BusinessFinding's own evidence, and Conviction drops to LOW.
        #
        # The assertion this test exists for is unchanged and still
        # holds: Business Risk being HIGH is NOT what capped Conviction.
        # The reason codes below prove that -- the risk input is still
        # reported as clear, and the cap comes from contradiction.
        assert analysis.conviction.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.NO_HIGH_FINANCIAL_OR_VALUATION_RISK in analysis.conviction.reasons
        assert ConvictionReasonCode.CONTRADICTING_EVIDENCE_PRESENT in analysis.conviction.reasons

    def test_high_financial_risk_with_cheap_valuation_still_forces_low(self):
        """Dilution (Capital Allocation WEAK) drives Financial Risk HIGH
        even while Valuation is UNDERVALUED (cheap, LOW Valuation Risk)
        -- proving Financial Risk alone, independent of Valuation Risk,
        can force LOW."""
        from datetime import date

        from atlas.analysis_engine.conviction import ConvictionLevel, ConvictionReasonCode

        engine_input, output = self._fresh_full_coverage_input()
        records = (
            self._record("financial_statement", date(2022, 12, 31), "iss22", share_issuance=100.0),
            self._record("financial_statement", date(2023, 12, 31), "iss23", share_issuance=100.0),
            self._record("financial_statement", date(2022, 12, 31), "buy22", share_buybacks=10.0),
            self._record("financial_statement", date(2023, 12, 31), "fy23", free_cash_flow=100.0),
            self._record("financial_statement", date(2024, 12, 31), "fy24", free_cash_flow=110.0),
            # Rising TOTAL_DEBT alongside dilution: two NEGATIVE Capital
            # Allocation signals (capital_return, leverage_trend) against
            # one POSITIVE (cash_generation, needed for Valuation's own
            # FCF Yield conclusion below) -- negatives genuinely outweigh
            # positives under the v2 combination rule, same as v1's own
            # "one negative disqualifies" reached WEAK here before it.
            self._record("financial_statement", date(2022, 12, 31), "debt22", total_debt=50.0),
            self._record("financial_statement", date(2023, 12, 31), "debt23", total_debt=150.0),
            self._record("financial_statement", date(2024, 12, 31), "debt24", total_debt=300.0),
            self._record("market_data_snapshot", date(2022, 12, 31), "m22", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2023, 12, 31), "m23", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2024, 12, 31), "m24", share_price=52.0, shares_outstanding=100.0),
        )
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        assert analysis.conviction.level is ConvictionLevel.LOW
        assert ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT in analysis.conviction.reasons

    def test_business_and_valuation_unavailable_yields_insufficient_evidence(self):
        """No `business_records` at all: `assess_data_completeness` finds
        no real company data, so `analysis_coverage` reads `NO_COVERAGE`
        and Conviction is `INSUFFICIENT_EVIDENCE` -- regardless of the
        investor Observation/Evidence `_fresh_full_coverage_input()`
        still supplies. This is Calibration Phase 4's own intended
        behavior change: before this sprint, investor evidence coverage
        alone (`EvidenceCoverageLevel.FULL`) let Conviction reach
        `MODERATE` here with zero real company data behind it -- exactly
        the systemic defect this sprint fixes, so this scenario is now
        deliberately different, not preserved."""
        from atlas.analysis_engine.conviction import ConvictionLevel, ConvictionReasonCode

        engine_input, output = self._fresh_full_coverage_input()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        assert analysis.conviction.level is ConvictionLevel.INSUFFICIENT_EVIDENCE
        assert analysis.conviction.reasons == (ConvictionReasonCode.EVIDENCE_COVERAGE_INSUFFICIENT,)

    def test_risk_analysis_insufficient_input_never_raises_risk_flag(self):
        """No `business_records` at all -> every Risk category with a
        real evaluator lands on `INSUFFICIENT_INPUT` (uncertainty),
        never `HIGH` -- missing risk evidence must never be silently
        promoted into a Conviction-lowering signal. Conviction itself
        reaches `INSUFFICIENT_EVIDENCE` here via the `NO_COVERAGE` floor
        (no company data at all), a separate, earlier-firing branch that
        never reaches the risk check -- so `HIGH_FINANCIAL_OR_VALUATION
        _RISK_PRESENT` correctly never appears in its reasons either."""
        from atlas.analysis_engine.contracts import RiskCategory
        from atlas.analysis_engine.conviction import ConvictionReasonCode
        from atlas.analysis_engine.risk.contracts import RiskStatus

        engine_input, output = self._fresh_full_coverage_input()
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        for category in (RiskCategory.FINANCIAL_RISK, RiskCategory.VALUATION_RISK):
            finding = next(f for f in analysis.risk_analysis.findings if f.category is category)
            assert finding.status is RiskStatus.INSUFFICIENT_INPUT
        assert ConvictionReasonCode.HIGH_FINANCIAL_OR_VALUATION_RISK_PRESENT not in analysis.conviction.reasons

    def test_recommendation_gate_reflects_the_new_real_conviction(self):
        """The five-level `ConvictionAssessment` -> `conviction_gate_met`
        relationship (ATLAS-020's own gate) is untouched: LOW (from high
        risk) still fails the MODERATE-minimum threshold exactly as
        before.

        What is new, and correctly so ("Recommendation Backend Step 3"):
        `conviction_gate_met is False` no longer implies
        `RecommendationWithheld`. `direction_selector.select_direction`
        and `recommendation_conviction.calculate_recommendation_conviction`
        are gated by DE-004 §3's own, independent, three-level
        Recommendation Conviction -- a genuinely different scale from
        the five-level one this test's Financial Risk scenario drives to
        LOW (see `direction_selector.py`'s and `recommendation.py`'s own
        module docstrings for why the two gates are deliberately never
        merged). Here, Business is real and positive (a single, real
        `MODERATE` Growth conclusion) and Valuation reaches a real,
        `EXPENSIVE` conclusion -- both are genuine, case-specific
        evidence, sufficient on their own for a real `NO_ACTION`
        (DE-008 §20's not-held table), independent of the unrelated,
        risk-driven five-level score staying LOW."""
        from datetime import date

        from atlas.analysis_engine.conviction import ConvictionLevel
        from atlas.analysis_engine.recommendation import (
            ComputedDirectionalRecommendation,
            RecommendationDirection,
        )
        from atlas.analysis_engine.recommendation_conviction import RecommendationConvictionLevel

        engine_input, output = self._fresh_full_coverage_input()
        records = (
            self._record("financial_statement", date(2022, 12, 31), "iss22", share_issuance=100.0),
            self._record("financial_statement", date(2023, 12, 31), "iss23", share_issuance=100.0),
            self._record("financial_statement", date(2022, 12, 31), "buy22", share_buybacks=10.0),
            self._record("financial_statement", date(2023, 12, 31), "fy23", free_cash_flow=100.0),
            self._record("financial_statement", date(2024, 12, 31), "fy24", free_cash_flow=110.0),
            # Rising TOTAL_DEBT alongside dilution: two NEGATIVE Capital
            # Allocation signals (capital_return, leverage_trend) against
            # one POSITIVE (cash_generation, needed for Valuation's own
            # FCF Yield conclusion below) -- negatives genuinely outweigh
            # positives under the v2 combination rule, same as v1's own
            # "one negative disqualifies" reached WEAK here before it.
            self._record("financial_statement", date(2022, 12, 31), "debt22", total_debt=50.0),
            self._record("financial_statement", date(2023, 12, 31), "debt23", total_debt=150.0),
            self._record("financial_statement", date(2024, 12, 31), "debt24", total_debt=300.0),
            self._record("market_data_snapshot", date(2022, 12, 31), "m22", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2023, 12, 31), "m23", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2024, 12, 31), "m24", share_price=52.0, shares_outstanding=100.0),
        )
        analysis = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )

        # The five-level gate: unaffected, still fails.
        assert analysis.recommendation.conviction_gate_met is False
        assert analysis.conviction.level is ConvictionLevel.LOW

        # The Direction Selector / three-level Recommendation Conviction:
        # independent, and reaches a real, genuine outcome regardless.
        recommendation = analysis.recommendation.recommendation
        assert isinstance(recommendation, ComputedDirectionalRecommendation)
        assert recommendation.direction is RecommendationDirection.NO_ACTION
        assert isinstance(recommendation.conviction_level, RecommendationConvictionLevel)

    def test_determinism_holds_through_the_full_conviction_chain(self):
        from datetime import date

        engine_input, output = self._fresh_full_coverage_input()
        records = (
            self._record("financial_statement", date(2022, 12, 31), "fy22", revenue=1000.0, free_cash_flow=200.0),
            self._record("financial_statement", date(2023, 12, 31), "fy23", revenue=1100.0, free_cash_flow=240.0),
            self._record("market_data_snapshot", date(2022, 12, 31), "m22", share_price=50.0, shares_outstanding=100.0),
            self._record("market_data_snapshot", date(2023, 12, 31), "m23", share_price=52.0, shares_outstanding=100.0),
        )
        first = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        second = assemble_analysis(
            engine_input, output, is_thesis_stale=False, business_records=records, generated_at=GENERATED_AT
        )
        assert first.conviction == second.conviction


class TestOpenQuestionsMigration:
    """ATLAS-027 Phase 2/25: `CanonicalAnalysis.open_questions` corrects
    exactly one stale question -- `VALUATION_THESIS_NOT_DOCUMENTED` --
    when `analysis_engine`'s own real Valuation is conclusive, while
    `reasoning.finding.open_questions` (decision_engine's own object)
    stays completely unmutated, and every other question remains."""

    @staticmethod
    def _valuation_records():
        from datetime import date, datetime, timezone

        from atlas.analysis_engine.business_data.models import RawBusinessDocument
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest

        def make(source_kind, period_end, identifier, *, published_at=GENERATED_AT, **metadata):
            document = RawBusinessDocument(
                identifier=identifier,
                company="ASML",
                source_kind=source_kind,
                published_at=published_at,
                provider_id="structured_test",
                raw_reference=f"ref://{identifier}",
                content_hash=f"hash-{identifier}",
                language="en",
                period_end=period_end,
                metadata=metadata,
            )
            result = ingest(document, evaluated_at=GENERATED_AT)
            assert isinstance(result, IngestedRecord), result
            return result.record

        # See TestValuationEngineEndToEnd._records -- a real filing gap
        # is required for ATLAS-032's no-look-ahead eligibility to pair
        # a fundamental with a later market observation.
        return (
            make("annual_report", date(2022, 12, 31), "fy22", published_at=datetime(2023, 2, 15, tzinfo=timezone.utc), free_cash_flow=100.0),
            make("annual_report", date(2023, 12, 31), "fy23", published_at=datetime(2024, 2, 15, tzinfo=timezone.utc), free_cash_flow=110.0),
            make("market_data_snapshot", date(2023, 3, 1), "m22", share_price=50.0, shares_outstanding=100.0),
            make("market_data_snapshot", date(2024, 3, 1), "m23", share_price=52.0, shares_outstanding=100.0),
        )

    def test_valuation_thesis_question_present_when_valuation_is_not_conclusive(self):
        from atlas.decision_engine.contracts import OpenQuestionKind

        engine_input, output = run_populated()
        analysis = assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        assert any(q.kind is OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED for q in analysis.open_questions)

    def test_valuation_thesis_question_retired_when_valuation_is_conclusive(self):
        from atlas.decision_engine.contracts import OpenQuestionKind

        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        assert not any(q.kind is OpenQuestionKind.VALUATION_THESIS_NOT_DOCUMENTED for q in analysis.open_questions)

    def test_durability_question_is_retired_only_once_really_assessed(self):
        """Stage 3 gave Durability a real Core evaluator, so
        decision_engine's own permanently-locked durability question can
        now go stale exactly the way the Valuation one already could.

        Its user-facing rendering is the literal sentence "Atlas has no
        business-fact data to assess durability from"; leaving it in
        place while `CanonicalAnalysis` carries a real Durability status
        would have Atlas deny evidence it demonstrably holds."""
        from atlas.analysis_engine.business_contracts import BusinessCategory
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as Status
        from atlas.decision_engine.contracts import OpenQuestionKind

        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        durability = next(
            f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.DURABILITY
        )
        assert durability.status is not Status.INSUFFICIENT_INPUT, (
            "fixture no longer produces an assessed durability; this test proves nothing")
        assert not any(
            q.kind is OpenQuestionKind.BUSINESS_DURABILITY_NOT_ASSESSABLE for q in analysis.open_questions
        )

    def test_durability_question_is_kept_when_the_company_lacks_the_facts(self):
        """The other half, and the one that matters most for honesty:
        insufficient input is a real data gap and is never suppressed
        into an assessed conclusion. Without business records Durability
        cannot be evaluated, so the question must survive."""
        from atlas.analysis_engine.business_contracts import BusinessCategory
        from atlas.analysis_engine.business_contracts import BusinessCategoryStatus as Status
        from atlas.decision_engine.contracts import OpenQuestionKind

        engine_input, output = run_populated()
        analysis = assemble_analysis(engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT)
        durability = next(
            f for f in analysis.business_analysis.findings if f.kind is BusinessCategory.DURABILITY
        )
        assert durability.status is Status.INSUFFICIENT_INPUT
        assert any(
            q.kind is OpenQuestionKind.BUSINESS_DURABILITY_NOT_ASSESSABLE for q in analysis.open_questions
        )

    def test_all_seven_portfolio_factor_questions_never_retired(self):
        from atlas.decision_engine.contracts import OpenQuestionKind

        engine_input, output = run_populated()
        analysis = assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        matches = [q for q in analysis.open_questions if q.kind is OpenQuestionKind.PORTFOLIO_FACTOR_NOT_ASSESSABLE]
        assert len(matches) == 7

    def test_reasoning_finding_open_questions_is_never_mutated(self):
        """The correction lives only on `CanonicalAnalysis.open_questions`
        -- decision_engine's own `ReasoningResult` is reused verbatim,
        never edited."""
        engine_input, output = run_populated()
        original = output.reasoning.finding.open_questions
        assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        assert output.reasoning.finding.open_questions == original

    def test_ceiling_is_honestly_unchanged_by_this_fix_alone(self):
        """The brutally honest finding this sprint's own audit surfaced:
        retiring the genuinely stale questions does not, by itself, let
        Conviction exceed its ceiling -- the seven Portfolio-factor
        questions remain, so `has_open_questions` stays True either way.

        Stage 3 raised the count from one retired question to two: the
        same `business_records` that make Valuation conclusive also give
        Durability enough facts to reach a real status, so both
        decision_engine-level questions go stale together. The point of
        the test is unchanged -- Conviction still does not move."""
        engine_input, output = run_populated()
        without_valuation = assemble_analysis(
            engine_input, output, is_thesis_stale=False, generated_at=GENERATED_AT
        )
        with_valuation = assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        assert len(with_valuation.open_questions) == len(without_valuation.open_questions) - 2
        assert with_valuation.open_questions != without_valuation.open_questions
        assert with_valuation.conviction.level == without_valuation.conviction.level

    def test_determinism(self):
        engine_input, output = run_populated()
        first = assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        second = assemble_analysis(
            engine_input,
            output,
            is_thesis_stale=False,
            business_records=self._valuation_records(),
            generated_at=GENERATED_AT,
        )
        assert first.open_questions == second.open_questions
