"""REST controller for the canonical Investment Case (ATLAS-029).

GET /cases/{case_id}/analysis - read the canonical Investment Case
analysis for one Case, powered by `InvestmentCaseCompositionService`
(ATLAS-027) rather than the older `case_intelligence` path.

A sibling route under the same `/cases` prefix `case_intelligence`'s own
`GET /cases/{case_id}/intelligence` already uses -- additive only. That
older endpoint is left running unmodified this sprint (still consumed by
`discovery_context`); this is the new source `InvestmentCasePage.tsx`
migrates to. 404 on a Case that does not exist, matching
`GET /cases/{case_id}` and `.../intelligence`'s own existing behavior.

**Atlas Intelligence Sprint 2 (Recommendation Quality & Actionability,
Deliverable 5).** This router, not `investment_case/api/schemas.py`
itself, is the one place `atlas.alpha.stance` is ever imported from this
package -- `atlas.alpha.stance` legitimately depends on
`InvestmentCaseCompositionService` (the same layering
`atlas.alpha.portfolio_fit` already established), so the dependency can
only run this direction: the router, as the real composition root, reads
a `Stance` from `StanceService` and hands `InvestmentCaseAnalysisView
.from_domain` an already-built `StanceView`, never a raw domain object
that schema module would otherwise need to import.

**Atlas Intelligence Sprint 3 (Decision Explainability & Evidence Trace,
Deliverable 4).** Same pattern one layer further: this router calls
`atlas.alpha.explainability.explain()` directly with the `Stance` it
already built above plus a freshly recomputed `CoverageAssessment` (a
pure, cheap function -- `schemas.py`'s own `from_domain` already
recomputes this same assessment a second time for the `coverage` field,
an accepted precedent, not a new cost this Sprint introduces). This
deliberately bypasses `ExplainabilityService` -- that service exists for
`atlas.alpha.explainability.api.router`'s own standalone endpoints,
where it must independently rebuild the full `InvestmentCaseComposition`
from scratch; here, that composition and that `Stance` already exist
one call above, so calling the engine function directly avoids a third,
wasteful full-case rebuild.

**Atlas Intelligence Sprint 4 (Evidence Quality & Conflict Resolution,
Deliverable 5).** Same pattern once more: this router calls
`atlas.alpha.evidence_quality.assess_evidence_quality()` directly,
reusing the same `composition.business_facts`/`.market_facts`
`from_domain` already computed above (no third recomputation) plus one
additional, genuinely new fetch this Sprint's own engine needs and no
earlier Sprint required: the *raw*, pre-conflict-drop `BusinessRecord`s
for this Case's ticker, via the same `SqlAlchemyBusinessRecordRepository`
`InvestmentCaseCompositionService` itself already depends on --
`InvestmentCaseComposition` only ever exposes the post-drop
`business_facts`/`market_facts`, never the raw records a conflict check
needs. Bypasses `EvidenceQualityService` for the same reason `explain()`
bypasses `ExplainabilityService` above: that service exists for
`evidence_quality.api.router`'s own standalone endpoints, which must
rebuild the whole composition from scratch; here it already exists.

**Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
Understanding, Deliverable 5).** This is the one, natural capture point
for `atlas.alpha.evidence_timeline`'s own new snapshot mechanism --
Coverage/Stance/Evidence Quality are already fully computed above for
this exact response, so this router calls `capture_evidence_snapshot()`
with them, reads the current persisted head via
`SqlAlchemyEvidenceSnapshotRepository.get_latest()`, compares with
`compare_evidence_snapshots()`, and persists the result with `.add()`
(idempotent by content hash -- a no-op when nothing changed since the
last capture, mirroring `InvestmentCaseCompositionService.build()`'s
own identical `AnalyticalSnapshot` capture one layer below). This is
the only place in the whole request that performs a write; every other
composition above it stays read-only.

**Atlas Intelligence -- Materiality & Priority Engine, Deliverable 5.**
Same pattern once more: this router calls
`atlas.alpha.materiality.assess_materiality()` directly with the
`Explanation` it already built above -- no new composition, no new
repository, the cheapest addition of any Sprint in this lineage.
Bypasses `MaterialityService` for the same reason `explain()` bypasses
`ExplainabilityService`: that service exists for `materiality.api
.router`'s own standalone endpoints, which must rebuild the whole
composition from scratch; here `Explanation` already exists.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.business_data_refresh.api.dependencies import get_business_record_repository
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.coverage import assess_coverage
from atlas.alpha.evidence_quality import assess_evidence_quality
from atlas.alpha.evidence_quality.models import EvidenceQualityReport
from atlas.alpha.knowledge_coverage import assess_knowledge_coverage
from atlas.alpha.knowledge_coverage.models import InvestmentCaseKnowledgeCoverage
from atlas.alpha.evidence_timeline import capture_evidence_snapshot, compare_evidence_snapshots, is_material_transition
from atlas.alpha.evidence_timeline.api.dependencies import get_evidence_snapshot_repository
from atlas.alpha.evidence_timeline.models import EvidenceHistory
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.explainability import explain
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.api.schemas import (
    ConfidenceReasonView,
    DimensionCoverageView,
    EvidenceConflictView,
    EvidenceQualityReportView,
    EvidenceTimelineView,
    EvidenceTransitionView,
    SourceEvidenceEventView,
    ExplanationView,
    FactQualityView,
    InvestmentCaseAnalysisView,
    InvestmentCaseKnowledgeCoverageView,
    CaseOperationalFreshnessView,
    MaterialEvidenceView,
    MaterialityAssessmentView,
    MonitoringStatusView,
    StanceReasonView,
    StanceView,
    UnsupportedFindingView,
)
from atlas.alpha.investment_case.models import InvestmentCaseComposition
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.explainability.models import Explanation
from atlas.alpha.materiality import assess_materiality
from atlas.alpha.materiality.models import MaterialityAssessment
from atlas.alpha.monitoring.api.dependencies import get_monitoring_result_repository, get_monitoring_service
from atlas.alpha.monitoring.engine import HIGH_IMPORTANCE_CATEGORIES
from atlas.alpha.monitoring.models import CaseOperationalFreshness, MonitoringMateriality, MonitoringResult
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository
from atlas.alpha.monitoring.service import MonitoringService
from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.stance.models import Stance
from atlas.alpha.stance.service import StanceService
from atlas.analysis_engine.business_data.versioning import latest_versions

router = APIRouter(prefix="/cases", tags=["investment-case"])


def _ticker_for_composition(composition: InvestmentCaseComposition) -> str | None:
    if composition.holding_context is not None:
        return composition.holding_context.ticker
    if composition.company_profile is not None:
        return composition.company_profile.ticker
    return None


def _stance_view(stance: Stance) -> StanceView:
    return StanceView(
        level=stance.level.value,
        reasoning=[StanceReasonView(code=r.code.value) for r in stance.reasoning],
        supporting_signals=[StanceReasonView(code=r.code.value) for r in stance.supporting_signals],
        limiting_signals=[StanceReasonView(code=r.code.value) for r in stance.limiting_signals],
        confidence=stance.confidence.value,
        missing_information=list(stance.missing_information),
    )


def _explanation_view(explanation: Explanation) -> ExplanationView:
    return ExplanationView(
        supporting_evidence=[StanceReasonView(code=r.code.value) for r in explanation.supporting_evidence],
        contradicting_evidence=[StanceReasonView(code=r.code.value) for r in explanation.contradicting_evidence],
        limiting_factors=[StanceReasonView(code=r.code.value) for r in explanation.limiting_factors],
        missing_evidence=[
            DimensionCoverageView(dimension=d.dimension, level=d.level.value, reasoning=list(d.reasoning))
            for d in explanation.missing_evidence
        ],
        confidence_drivers=[
            ConfidenceReasonView(code=r.code.value, count=r.count, total=r.total)
            for r in explanation.confidence_drivers
        ],
        most_valuable_missing_information=(
            DimensionCoverageView(
                dimension=explanation.most_valuable_missing_information.dimension,
                level=explanation.most_valuable_missing_information.level.value,
                reasoning=list(explanation.most_valuable_missing_information.reasoning),
            )
            if explanation.most_valuable_missing_information is not None
            else None
        ),
    )


def _evidence_quality_view(report: EvidenceQualityReport) -> EvidenceQualityReportView:
    return EvidenceQualityReportView(
        quality=report.quality.value,
        conflict_status=report.conflict_status.value,
        freshness=report.freshness.value,
        dominance=report.dominance.value,
        warnings=[w.value for w in report.warnings],
        facts=[
            FactQualityView(
                fact_kind=f.fact_kind,
                freshness=f.freshness.value,
                dominance=f.dominance.value,
                latest_period=f.latest_period,
                latest_published_at=f.latest_published_at,
                source_record_count=f.source_record_count,
            )
            for f in report.facts
        ],
        conflicts=[
            EvidenceConflictView(
                fact_kind=c.fact_kind,
                period=c.period,
                unit=c.unit,
                values=list(c.values),
                source_record_ids=list(c.source_record_ids),
            )
            for c in report.conflicts
        ],
        unsupported_findings=[UnsupportedFindingView(category=f.category, status=f.status) for f in report.unsupported_findings],
    )


def _knowledge_coverage_view(coverage: InvestmentCaseKnowledgeCoverage) -> InvestmentCaseKnowledgeCoverageView:
    return InvestmentCaseKnowledgeCoverageView.from_domain(coverage)


def _evidence_timeline_view(history: EvidenceHistory) -> EvidenceTimelineView:
    return EvidenceTimelineView(
        is_baseline=history.is_baseline,
        transitions=[
            EvidenceTransitionView(
                id=t.id,
                category=t.category.value,
                direction=t.direction.value,
                previous_state=t.previous_state,
                current_state=t.current_state,
                is_material=is_material_transition(t),
            )
            for t in history.transitions
        ],
        new_source_evidence=[SourceEvidenceEventView(fact_kind=e.fact_kind, period=e.period) for e in history.new_source_evidence],
        previous_captured_at=history.previous_captured_at,
        current_captured_at=history.current_captured_at,
    )


def _material_evidence_view(item) -> MaterialEvidenceView:
    return MaterialEvidenceView(reason=StanceReasonView(code=item.reason.code.value), materiality=item.materiality.value)


def _materiality_view(assessment: MaterialityAssessment) -> MaterialityAssessmentView:
    return MaterialityAssessmentView(
        supporting_evidence=[_material_evidence_view(i) for i in assessment.supporting_evidence],
        contradicting_evidence=[_material_evidence_view(i) for i in assessment.contradicting_evidence],
        limiting_factors=[_material_evidence_view(i) for i in assessment.limiting_factors],
        top_supporting_evidence=_material_evidence_view(assessment.top_supporting_evidence) if assessment.top_supporting_evidence is not None else None,
        top_contradicting_evidence=_material_evidence_view(assessment.top_contradicting_evidence) if assessment.top_contradicting_evidence is not None else None,
        top_limiting_factor=_material_evidence_view(assessment.top_limiting_factor) if assessment.top_limiting_factor is not None else None,
        top_missing_evidence=(
            DimensionCoverageView(
                dimension=assessment.top_missing_evidence.dimension,
                level=assessment.top_missing_evidence.level.value,
                reasoning=list(assessment.top_missing_evidence.reasoning),
            )
            if assessment.top_missing_evidence is not None
            else None
        ),
    )


def _monitoring_status_view(result: MonitoringResult) -> MonitoringStatusView:
    """Sprint 7, Deliverable 13 -- picks the single most important
    change to lead with: material, `HIGH_IMPORTANCE_CATEGORIES` first,
    tie-broken by id for determinism. `None` reason when `changes` is
    empty (an honest up-to-date/waiting state, never a fabricated
    sentence)."""
    material_changes = [c for c in result.changes if c.materiality is MonitoringMateriality.MATERIAL]
    leading = sorted(
        material_changes,
        key=lambda c: (0 if c.category in HIGH_IMPORTANCE_CATEGORIES else 1, c.id),
    )
    return MonitoringStatusView(
        status=result.status.value,
        material_change_count=len(material_changes),
        latest_change_reason=leading[0].reason if leading else None,
        generated_at=result.generated_at,
    )


def _operational_freshness_view(freshness: CaseOperationalFreshness) -> CaseOperationalFreshnessView:
    return CaseOperationalFreshnessView(
        is_pending=freshness.is_pending,
        last_monitored_at=freshness.last_monitored_at,
        last_run_failed_for_case=freshness.last_run_failed_for_case,
        data_freshness_status=freshness.data_freshness_status.value,
    )


@router.get("/{case_id}/analysis", response_model=InvestmentCaseAnalysisView)
def get_investment_case_analysis(
    case_id: str,
    service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
    stance_service: StanceService = Depends(get_stance_service),
    business_record_repository: SqlAlchemyBusinessRecordRepository = Depends(get_business_record_repository),
    evidence_snapshot_repository: SqlAlchemyEvidenceSnapshotRepository = Depends(get_evidence_snapshot_repository),
    monitoring_result_repository: SqlAlchemyMonitoringResultRepository = Depends(get_monitoring_result_repository),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
) -> InvestmentCaseAnalysisView:
    composition = service.build(case_id)
    if composition is None:
        raise HTTPException(status_code=404, detail="Case not found")
    stance = stance_service.assess_for_case(case_id)
    coverage = assess_coverage(composition.canonical_analysis, is_thesis_stale=composition.is_thesis_stale)
    explanation = explain(stance, coverage) if stance is not None else None

    ticker = _ticker_for_composition(composition)
    records = latest_versions(business_record_repository.get_by_company(ticker)) if ticker is not None else ()
    evidence_quality = assess_evidence_quality(
        records,
        composition.business_facts,
        composition.market_facts,
        composition.canonical_analysis,
        evaluated_at=composition.generated_at,
    )
    knowledge_coverage = assess_knowledge_coverage(
        composition, evidence_quality, records, evaluated_at=composition.generated_at
    )

    evidence_snapshot = capture_evidence_snapshot(
        coverage,
        evidence_quality,
        stance,
        composition.business_facts,
        composition.market_facts,
        captured_at=composition.generated_at,
    )
    previous_evidence_snapshot = evidence_snapshot_repository.get_latest(case_id)
    evidence_history = compare_evidence_snapshots(previous_evidence_snapshot, evidence_snapshot)
    evidence_snapshot_repository.add(case_id, evidence_snapshot, evidence_history)

    materiality = assess_materiality(explanation) if explanation is not None else None

    # Sprint 7, Deliverable 13 -- read-only: this endpoint never
    # triggers a Monitoring run of its own (see `atlas.alpha.monitoring
    # .service`'s own module docstring on why `run()` stays an explicit,
    # separately-triggered operation). `None` when Monitoring has never
    # evaluated this Case yet -- an honest "not evaluated," not a
    # fabricated "up to date."
    monitoring_result = monitoring_result_repository.get(case_id)

    # Sprint 8, Deliverable 15 -- purely operational, computed via the
    # same cheap pre-pass `run()` itself uses (see `MonitoringService
    # ._signal_maps`), never mixed into `monitoring` above.
    operational_freshness = monitoring_service.freshness_for_case(case_id)

    return InvestmentCaseAnalysisView.from_domain(
        composition,
        stance=_stance_view(stance) if stance is not None else None,
        explanation=_explanation_view(explanation) if explanation is not None else None,
        evidence_quality_report=_evidence_quality_view(evidence_quality),
        evidence_timeline=_evidence_timeline_view(evidence_history),
        materiality=_materiality_view(materiality) if materiality is not None else None,
        monitoring=_monitoring_status_view(monitoring_result) if monitoring_result is not None else None,
        operational_freshness=_operational_freshness_view(operational_freshness),
        knowledge_coverage=_knowledge_coverage_view(knowledge_coverage),
    )
