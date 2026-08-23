"""HTTP response schemas for the Knowledge Orchestration API. Wire
format is camelCase via the shared Core `CamelModel` (ADR-004),
matching every other Alpha schema module -- mirrors `atlas.alpha
.ingestion.api.schemas.IngestionResultView`'s own shape. Every field
is a direct read of an already-computed `OrchestrationOutcome`;
nothing recomputed here.
"""
from __future__ import annotations

from atlas.alpha.knowledge_orchestration.orchestrator import AcquisitionStepOutcome, OrchestrationOutcome
from atlas.alpha.knowledge_orchestration.planner import AcquisitionPlanItem
from atlas.core.infrastructure.api.serialization import CamelModel


class AcquisitionPlanItemView(CamelModel):
    domain: str
    provider_id: str
    criticality: str
    reason: str
    relevance: str
    impact_reasons: list[str]

    @classmethod
    def from_domain(cls, item: AcquisitionPlanItem) -> "AcquisitionPlanItemView":
        return cls(
            domain=item.domain.value,
            provider_id=item.provider_id,
            criticality=item.criticality.value,
            reason=item.reason.value,
            relevance=item.relevance.value,
            impact_reasons=[reason.value for reason in item.impact_reasons],
        )


class AcquisitionStepOutcomeView(CamelModel):
    item: AcquisitionPlanItemView
    fetched_documents: int
    new_records: int
    new_versions: int
    duplicates_skipped: int
    rejected_documents: int
    provider_errors: list[str]
    identity_gate_outcome: str
    domain_acquired: bool

    @classmethod
    def from_domain(cls, step: AcquisitionStepOutcome) -> "AcquisitionStepOutcomeView":
        summary = step.summary
        return cls(
            item=AcquisitionPlanItemView.from_domain(step.item),
            fetched_documents=summary.fetched_documents,
            new_records=summary.new_records,
            new_versions=summary.new_versions,
            duplicates_skipped=summary.duplicates_skipped,
            rejected_documents=summary.rejected_documents,
            provider_errors=[f"{failure.provider_id}: {failure.error}" for failure in summary.provider_errors],
            identity_gate_outcome=summary.identity_gate_outcome,
            domain_acquired=step.domain_acquired,
        )


class OrchestrationOutcomeView(CamelModel):
    ticker: str
    case_id: str | None
    is_sufficient: bool
    sufficiency_reason: str
    planned_items: list[AcquisitionPlanItemView]
    steps: list[AcquisitionStepOutcomeView]
    acquired_domains: list[str]
    should_reanalyze: bool
    research_completion: str

    @classmethod
    def from_domain(cls, ticker: str, case_id: str | None, outcome: OrchestrationOutcome) -> "OrchestrationOutcomeView":
        return cls(
            ticker=ticker,
            case_id=case_id,
            is_sufficient=outcome.plan.sufficiency.is_sufficient,
            sufficiency_reason=outcome.plan.sufficiency.reason.value,
            planned_items=[AcquisitionPlanItemView.from_domain(item) for item in outcome.ordered_items],
            steps=[AcquisitionStepOutcomeView.from_domain(step) for step in outcome.steps],
            acquired_domains=[d.value for d in outcome.acquired_domains],
            should_reanalyze=outcome.should_reanalyze,
            research_completion=outcome.research_completion.outcome.value,
        )
