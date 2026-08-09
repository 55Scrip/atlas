"""Shared test fixtures for the Risk Analysis test suite (ATLAS-025)."""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.analysis_engine.business_contracts import (
    BusinessAnalysisResult,
    BusinessCategory,
    BusinessCategoryStatus,
    BusinessFinding,
)
from atlas.analysis_engine.business_contracts import severity_for_status as business_severity
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Provenance, SourceKind, UpdateTrigger
from atlas.analysis_engine.valuation.contracts import ValuationMethodKind, ValuationStatus
from atlas.analysis_engine.valuation.contracts import severity_for_valuation_status as valuation_severity
from atlas.analysis_engine.valuation.models import ValuationEngineResult, ValuationFinding
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.decision_engine.contracts import (
    ContradictionSummary,
    EvaluationState,
    EvidenceCoverageLevel,
    ObservationEpistemicStatus,
    ObservationEvidenceClassification,
)

EVALUATED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)

_COUNTER = iter(range(1_000_000))


def _prov() -> Provenance:
    return Provenance(
        source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
        source_references=(),
        dependencies=(),
        update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
        consumers=(),
        computed_at=EVALUATED_AT,
    )


def business_fact(kind: BusinessFactKind, value: float, period: str) -> BusinessFact:
    i = next(_COUNTER)
    return BusinessFact(
        id=f"fact-{i}",
        company="ASML",
        kind=kind,
        value=value,
        unit="usd",
        period=period,
        source_record_id=f"record-{i}",
        provenance=_prov(),
        extracted_at=EVALUATED_AT,
        published_at=EVALUATED_AT,
    )


def growth_finding(status: BusinessCategoryStatus, *, confidence: EvidenceCoverageLevel = EvidenceCoverageLevel.FULL) -> BusinessFinding:
    return BusinessFinding(
        id="business_finding:growth",
        kind=BusinessCategory.GROWTH,
        status=status,
        severity=business_severity(status),
        supporting_evidence=(),
        contradicting_evidence=(),
        missing_evidence=(),
        confidence=confidence,
        provenance=_prov(),
        updated_at=EVALUATED_AT,
    )


def capital_allocation_finding(
    status: BusinessCategoryStatus, *, confidence: EvidenceCoverageLevel = EvidenceCoverageLevel.FULL
) -> BusinessFinding:
    return BusinessFinding(
        id="business_finding:capital_allocation",
        kind=BusinessCategory.CAPITAL_ALLOCATION,
        status=status,
        severity=business_severity(status),
        supporting_evidence=(),
        contradicting_evidence=(),
        missing_evidence=(),
        confidence=confidence,
        provenance=_prov(),
        updated_at=EVALUATED_AT,
    )


def fcf_yield_finding(
    status: ValuationStatus, *, confidence: EvidenceCoverageLevel = EvidenceCoverageLevel.FULL
) -> ValuationFinding:
    return ValuationFinding(
        id="valuation_finding:fcf_yield_relative",
        kind=ValuationMethodKind.FCF_YIELD_RELATIVE,
        status=status,
        severity=valuation_severity(status),
        supporting_facts=(),
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=(),
        confidence=confidence,
        provenance=_prov(),
        evaluated_at=EVALUATED_AT,
    )


def _other_business_finding(category: BusinessCategory) -> BusinessFinding:
    status = BusinessCategoryStatus.INSUFFICIENT_INPUT
    return BusinessFinding(
        id=f"business_finding:{category.value}",
        kind=category,
        status=status,
        severity=business_severity(status),
        supporting_evidence=(),
        contradicting_evidence=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
        provenance=_prov(),
        updated_at=EVALUATED_AT,
    )


def business_analysis_result(
    *, growth: BusinessCategoryStatus, capital_allocation: BusinessCategoryStatus
) -> BusinessAnalysisResult:
    """All six categories, always -- `BUSINESS_MODEL`/`COMPETITIVE_POSITION`/
    `MANAGEMENT`/`DURABILITY` default to `INSUFFICIENT_INPUT`, matching
    `BusinessAnalysisResult`'s own invariant."""
    findings = tuple(
        growth_finding(growth)
        if category is BusinessCategory.GROWTH
        else capital_allocation_finding(capital_allocation)
        if category is BusinessCategory.CAPITAL_ALLOCATION
        else _other_business_finding(category)
        for category in BusinessCategory
    )
    return BusinessAnalysisResult(state=EvaluationState.EVALUATED, findings=findings)


def _scenario_finding(kind: ValuationMethodKind) -> ValuationFinding:
    status = ValuationStatus.INSUFFICIENT_INPUT
    return ValuationFinding(
        id=f"valuation_finding:{kind.value}",
        kind=kind,
        status=status,
        severity=valuation_severity(status),
        supporting_facts=(),
        contradicting_facts=(),
        assumptions=(),
        missing_evidence=(),
        confidence=EvidenceCoverageLevel.NOT_APPLICABLE,
        provenance=_prov(),
        evaluated_at=EVALUATED_AT,
    )


def valuation_engine_result(*, fcf_yield: ValuationStatus) -> ValuationEngineResult:
    """All four methods, always -- the three scenario methods default to
    `INSUFFICIENT_INPUT`, matching `ValuationEngineResult`'s own
    invariant (and today's real, honest behavior)."""
    findings = tuple(
        fcf_yield_finding(fcf_yield)
        if kind is ValuationMethodKind.FCF_YIELD_RELATIVE
        else _scenario_finding(kind)
        for kind in ValuationMethodKind
    )
    return ValuationEngineResult(state=EvaluationState.EVALUATED, findings=findings)


def classification(status: ObservationEpistemicStatus, *, challenging_count: int = 0) -> ObservationEvidenceClassification:
    return ObservationEvidenceClassification(
        observation_id=ObservationId(),
        status=status,
        supporting_evidence_count=0,
        challenging_evidence_count=challenging_count,
    )


def contradiction_summary(*classifications: ObservationEvidenceClassification) -> ContradictionSummary:
    return ContradictionSummary(observation_classifications=classifications)


__all__ = [
    "EVALUATED_AT",
    "EvaluationState",
    "business_fact",
    "growth_finding",
    "capital_allocation_finding",
    "fcf_yield_finding",
    "business_analysis_result",
    "valuation_engine_result",
    "classification",
    "contradiction_summary",
]
