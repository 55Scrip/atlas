"""Tests for `atlas.analysis_engine.business` (ATLAS-021) -- structural
completeness of the six-category taxonomy, Durability reuse (not
recomputation), missing-evidence honesty, and the extensibility slot
(`external_records`) actually working end to end rather than being
decorative."""
from __future__ import annotations

from atlas.analysis_engine.business import (
    BusinessAnalysisResult,
    BusinessCategory,
    BusinessCategoryStatus,
    BusinessDataGapKind,
    BusinessFinding,
    ExternalBusinessRecord,
    evaluate_business_analysis,
)
from atlas.analysis_engine.business_data.sources import SourceKind as DocumentSourceKind
from atlas.analysis_engine.exceptions import AnalysisEngineContractError
from atlas.analysis_engine.provenance import SourceKind
from atlas.core.domain.evidence.value_objects import Direction
from atlas.decision_engine.contracts import EvaluationState, EvidenceCoverageLevel
from tests.unit.analysis_engine._fixtures import GENERATED_AT, run_minimal, run_populated


class TestStructuralCompleteness:
    def test_all_six_categories_are_always_present(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        assert {f.kind for f in result.findings} == set(BusinessCategory)
        assert len(result.findings) == 6

    def test_state_is_always_evaluated(self):
        """Assembling six honest INSUFFICIENT_INPUT conclusions is
        itself a real result -- the same principle ReasoningResult
        already established."""
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        assert result.state is EvaluationState.EVALUATED

    def test_populated_case_produces_the_same_six_categories(self):
        """More Observations/Evidence on the Case does not change which
        categories exist -- Core evidence has no category-attribution
        field (see module docstring), so category coverage is
        independent of Case activity."""
        _, output = run_populated()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        assert {f.kind for f in result.findings} == set(BusinessCategory)


class TestNoFabrication:
    def test_no_category_ever_reaches_weak_moderate_or_strong_without_records(self):
        _, output = run_populated()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        for finding in result.findings:
            assert finding.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_status_stays_insufficient_input_even_with_external_records(self):
        """The central no-fabrication guarantee: presence of external
        records changes confidence and evidence references, never the
        strength verdict -- counting records is not business judgment."""
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.FINANCIAL_STATEMENT,
                category=BusinessCategory.GROWTH,
                direction=Direction.SUPPORTS,
                reference="statement-1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        growth = next(f for f in result.findings if f.kind is BusinessCategory.GROWTH)
        assert growth.status is BusinessCategoryStatus.INSUFFICIENT_INPUT

    def test_no_numeric_score_field_exists_anywhere(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        for finding in result.findings:
            assert not hasattr(finding, "score")
            assert not hasattr(finding, "weight")
            assert isinstance(finding.status.value, str)


class TestDurabilityIsReusedNotRecomputed:
    def test_durability_finding_matches_decision_engines_own_reason(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        durability = next(f for f in result.findings if f.kind is BusinessCategory.DURABILITY)
        assert durability.status is BusinessCategoryStatus.INSUFFICIENT_INPUT
        assert durability.provenance.source_kind is SourceKind.DECISION_ENGINE_STAGE

    def test_other_five_categories_are_analysis_engine_native(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        for finding in result.findings:
            if finding.kind is not BusinessCategory.DURABILITY:
                assert finding.provenance.source_kind is SourceKind.ANALYSIS_ENGINE_STAGE

    def test_durability_provenance_depends_on_the_reused_finding(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        durability = next(f for f in result.findings if f.kind is BusinessCategory.DURABILITY)
        assert durability.provenance.dependencies == ("business_analysis_unavailable",)


class TestMissingEvidenceIsFirstClass:
    def test_every_category_names_a_real_missing_evidence_reason_by_default(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        for finding in result.findings:
            assert finding.missing_evidence == (BusinessDataGapKind.NO_EXTERNAL_DATA_SOURCE_CONNECTED,)

    def test_confidence_is_not_applicable_by_default(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        for finding in result.findings:
            assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_missing_evidence_reason_changes_once_a_record_is_supplied(self):
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.COMPANY_FILING,
                category=BusinessCategory.MANAGEMENT,
                direction=Direction.CHALLENGES,
                reference="filing-1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        management = next(f for f in result.findings if f.kind is BusinessCategory.MANAGEMENT)
        assert management.missing_evidence == (BusinessDataGapKind.EXTERNAL_DATA_NOT_YET_INTERPRETED,)
        untouched = next(f for f in result.findings if f.kind is BusinessCategory.GROWTH)
        assert untouched.missing_evidence == (BusinessDataGapKind.NO_EXTERNAL_DATA_SOURCE_CONNECTED,)


class TestExtensibility:
    """Proves the `external_records` slot is real wiring, not a
    decorative parameter -- exactly the property ATLAS-021 required:
    future ingestion should be additive, never a redesign."""

    def test_supporting_record_populates_supporting_evidence(self):
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.ANNUAL_REPORT,
                category=BusinessCategory.CAPITAL_ALLOCATION,
                direction=Direction.SUPPORTS,
                reference="report-1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        finding = next(f for f in result.findings if f.kind is BusinessCategory.CAPITAL_ALLOCATION)
        assert finding.supporting_evidence == ("report-1",)
        assert finding.contradicting_evidence == ()
        assert finding.confidence is EvidenceCoverageLevel.FULL
        assert finding.provenance.source_kind is SourceKind.EXTERNAL_DATA_SOURCE

    def test_challenging_record_populates_contradicting_evidence(self):
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.NEWS,
                category=BusinessCategory.COMPETITIVE_POSITION,
                direction=Direction.CHALLENGES,
                reference="news-1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        finding = next(f for f in result.findings if f.kind is BusinessCategory.COMPETITIVE_POSITION)
        assert finding.contradicting_evidence == ("news-1",)
        assert finding.supporting_evidence == ()

    def test_records_are_routed_to_the_correct_category_only(self):
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.MACRO_REPORT,
                category=BusinessCategory.BUSINESS_MODEL,
                direction=Direction.SUPPORTS,
                reference="macro-1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        for finding in result.findings:
            if finding.kind is BusinessCategory.BUSINESS_MODEL:
                assert finding.supporting_evidence == ("macro-1",)
            else:
                assert finding.supporting_evidence == ()
                assert finding.confidence is EvidenceCoverageLevel.NOT_APPLICABLE

    def test_multiple_records_same_category_are_all_captured(self):
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.QUARTERLY_REPORT,
                category=BusinessCategory.GROWTH,
                direction=Direction.SUPPORTS,
                reference="q1",
            ),
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.QUARTERLY_REPORT,
                category=BusinessCategory.GROWTH,
                direction=Direction.SUPPORTS,
                reference="q2",
            ),
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.TRANSCRIPT,
                category=BusinessCategory.GROWTH,
                direction=Direction.CHALLENGES,
                reference="t1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        finding = next(f for f in result.findings if f.kind is BusinessCategory.GROWTH)
        assert set(finding.supporting_evidence) == {"q1", "q2"}
        assert finding.contradicting_evidence == ("t1",)

    def test_durability_can_also_receive_external_records(self):
        """Durability is reused from decision_engine by default, but the
        taxonomy is uniform -- a future filing tagged DURABILITY folds
        in exactly like any other category."""
        _, output = run_minimal()
        records = (
            ExternalBusinessRecord(
                source_kind=DocumentSourceKind.COMPANY_FILING,
                category=BusinessCategory.DURABILITY,
                direction=Direction.SUPPORTS,
                reference="filing-durability-1",
            ),
        )
        result = evaluate_business_analysis(
            output.business_evaluation, external_records=records, evaluated_at=GENERATED_AT
        )
        durability = next(f for f in result.findings if f.kind is BusinessCategory.DURABILITY)
        assert durability.supporting_evidence == ("filing-durability-1",)
        assert durability.provenance.source_kind is SourceKind.EXTERNAL_DATA_SOURCE


class TestContractValidation:
    def test_business_analysis_result_rejects_a_partial_category_list(self):
        incomplete = (
            BusinessFinding(
                id="x",
                kind=BusinessCategory.GROWTH,
                status=BusinessCategoryStatus.INSUFFICIENT_INPUT,
                severity=None,  # type: ignore[arg-type]
                supporting_evidence=(),
                contradicting_evidence=(),
                missing_evidence=(),
                confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
                provenance=None,  # type: ignore[arg-type]
                updated_at=GENERATED_AT,
            ),
        )
        try:
            BusinessAnalysisResult(state=EvaluationState.EVALUATED, findings=incomplete)
            assert False, "expected AnalysisEngineContractError"
        except AnalysisEngineContractError:
            pass

    def test_evaluate_business_analysis_requires_an_evaluated_business_evaluation(self):
        from atlas.decision_engine.contracts import BusinessEvaluationResult, StageNotImplementedReason

        not_evaluated = BusinessEvaluationResult(
            state=EvaluationState.NOT_EVALUATED,
            reason=StageNotImplementedReason.EVALUATOR_NOT_IMPLEMENTED,
        )
        try:
            evaluate_business_analysis(not_evaluated, evaluated_at=GENERATED_AT)
            assert False, "expected AnalysisEngineContractError"
        except AnalysisEngineContractError:
            pass


class TestDeterminism:
    def test_identical_inputs_produce_a_deeply_equal_result(self):
        _, output = run_populated()
        first = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        second = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        assert first == second

    def test_finding_ids_are_deterministic_and_unique(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        ids = [f.id for f in result.findings]
        assert len(ids) == len(set(ids))
        assert all(fid.startswith("business_finding:") for fid in ids)


class TestBusinessRecordsAwareness:
    """ATLAS-022 Phase 9: Business Analysis becomes aware that raw
    `business_data.models.BusinessRecord` documents exist, without
    fabricating any per-category attribution from them."""

    def test_defaults_to_no_available_records(self):
        _, output = run_minimal()
        result = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        assert result.available_business_records == ()

    def test_supplied_business_records_are_surfaced_by_id(self):
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
        from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

        _, output = run_minimal()
        ingested = ingest(build_raw_document(), evaluated_at=GENERATED_AT)
        assert isinstance(ingested, IngestedRecord)

        result = evaluate_business_analysis(
            output.business_evaluation,
            business_records=(ingested.record,),
            evaluated_at=GENERATED_AT,
        )
        assert result.available_business_records == (ingested.record.id,)

    def test_available_business_records_never_changes_any_category_status(self):
        """The central no-fabrication guarantee for this field: a
        BusinessRecord carries no category attribution, so its presence
        must never move any category off INSUFFICIENT_INPUT."""
        from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
        from tests.unit.analysis_engine.business_data._fixtures import build_raw_document

        _, output = run_minimal()
        ingested = ingest(build_raw_document(), evaluated_at=GENERATED_AT)
        assert isinstance(ingested, IngestedRecord)

        without_records = evaluate_business_analysis(output.business_evaluation, evaluated_at=GENERATED_AT)
        with_records = evaluate_business_analysis(
            output.business_evaluation,
            business_records=(ingested.record,),
            evaluated_at=GENERATED_AT,
        )
        without_statuses = {f.kind: f.status for f in without_records.findings}
        with_statuses = {f.kind: f.status for f in with_records.findings}
        assert without_statuses == with_statuses
