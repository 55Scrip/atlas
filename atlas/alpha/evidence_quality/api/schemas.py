"""HTTP response schemas for the Evidence Quality API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.evidence_quality.models import (
    EvidenceConflict,
    EvidenceQualityReport,
    FactQuality,
    UnsupportedFinding,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class EvidenceConflictView(CamelModel):
    fact_kind: str
    period: str
    unit: str
    values: list[float]
    source_record_ids: list[str]

    @classmethod
    def from_domain(cls, conflict: EvidenceConflict) -> "EvidenceConflictView":
        return cls(
            fact_kind=conflict.fact_kind,
            period=conflict.period,
            unit=conflict.unit,
            values=list(conflict.values),
            source_record_ids=list(conflict.source_record_ids),
        )


class FactQualityView(CamelModel):
    fact_kind: str
    freshness: str
    dominance: str
    latest_period: str | None
    latest_published_at: datetime | None
    source_record_count: int

    @classmethod
    def from_domain(cls, fact: FactQuality) -> "FactQualityView":
        return cls(
            fact_kind=fact.fact_kind,
            freshness=fact.freshness.value,
            dominance=fact.dominance.value,
            latest_period=fact.latest_period,
            latest_published_at=fact.latest_published_at,
            source_record_count=fact.source_record_count,
        )


class UnsupportedFindingView(CamelModel):
    category: str
    status: str

    @classmethod
    def from_domain(cls, finding: UnsupportedFinding) -> "UnsupportedFindingView":
        return cls(category=finding.category, status=finding.status)


class EvidenceQualityReportView(CamelModel):
    quality: str
    conflict_status: str
    freshness: str
    dominance: str
    warnings: list[str]
    facts: list[FactQualityView]
    conflicts: list[EvidenceConflictView]
    unsupported_findings: list[UnsupportedFindingView]

    @classmethod
    def from_domain(cls, report: EvidenceQualityReport) -> "EvidenceQualityReportView":
        return cls(
            quality=report.quality.value,
            conflict_status=report.conflict_status.value,
            freshness=report.freshness.value,
            dominance=report.dominance.value,
            warnings=[w.value for w in report.warnings],
            facts=[FactQualityView.from_domain(f) for f in report.facts],
            conflicts=[EvidenceConflictView.from_domain(c) for c in report.conflicts],
            unsupported_findings=[UnsupportedFindingView.from_domain(f) for f in report.unsupported_findings],
        )


class TickerEvidenceQualityView(CamelModel):
    ticker: str
    report: EvidenceQualityReportView
