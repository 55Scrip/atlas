"""HTTP response schemas for the Business Quality Assessment API. Wire
format is camelCase via the shared Core `CamelModel` (ADR-004), matching
every other Alpha schema module. Every enum is sent as its `.value`
string -- the frontend owns localized labels via its own key map, the
same convention every other categorical field in this codebase already
follows.
"""
from __future__ import annotations

from atlas.alpha.business_quality_assessment.models import (
    BusinessQualityAssessment,
    BusinessQualityDriver,
    ManagementAssessment,
    ManagementDimensionAssessment,
    MoatAssessment,
    ReinvestmentAssessment,
)
from atlas.core.infrastructure.api.serialization import CamelModel

__all__ = [
    "MoatAssessmentView",
    "ManagementDimensionAssessmentView",
    "ManagementAssessmentView",
    "ReinvestmentAssessmentView",
    "BusinessQualityDriverView",
    "BusinessQualityAssessmentView",
]


class MoatAssessmentView(CamelModel):
    level: str
    supporting_evidence: list[str]
    unassessed_dimensions: list[str]

    @classmethod
    def from_domain(cls, moat: MoatAssessment) -> "MoatAssessmentView":
        return cls(
            level=moat.level.value,
            supporting_evidence=[e.value for e in moat.supporting_evidence],
            unassessed_dimensions=list(moat.unassessed_dimensions),
        )


class ManagementDimensionAssessmentView(CamelModel):
    kind: str
    level: str

    @classmethod
    def from_domain(cls, dimension: ManagementDimensionAssessment) -> "ManagementDimensionAssessmentView":
        return cls(kind=dimension.kind.value, level=dimension.level.value)


class ManagementAssessmentView(CamelModel):
    level: str
    dimensions: list[ManagementDimensionAssessmentView]
    unassessed_dimensions: list[str]

    @classmethod
    def from_domain(cls, management: ManagementAssessment) -> "ManagementAssessmentView":
        return cls(
            level=management.level.value,
            dimensions=[ManagementDimensionAssessmentView.from_domain(d) for d in management.dimensions],
            unassessed_dimensions=list(management.unassessed_dimensions),
        )


class ReinvestmentAssessmentView(CamelModel):
    level: str
    supporting_evidence: list[str]
    unassessed_dimensions: list[str]

    @classmethod
    def from_domain(cls, reinvestment: ReinvestmentAssessment) -> "ReinvestmentAssessmentView":
        return cls(
            level=reinvestment.level.value,
            supporting_evidence=[e.value for e in reinvestment.supporting_evidence],
            unassessed_dimensions=list(reinvestment.unassessed_dimensions),
        )


class BusinessQualityDriverView(CamelModel):
    kind: str
    source: str

    @classmethod
    def from_domain(cls, driver: BusinessQualityDriver) -> "BusinessQualityDriverView":
        return cls(kind=driver.kind.value, source=driver.source)


class BusinessQualityAssessmentView(CamelModel):
    moat: MoatAssessmentView
    management: ManagementAssessmentView
    reinvestment: ReinvestmentAssessmentView
    overall_level: str
    strengths: list[BusinessQualityDriverView]
    weaknesses: list[BusinessQualityDriverView]
    greatest_advantage: BusinessQualityDriverView | None
    greatest_concern: BusinessQualityDriverView | None
    unknowns: list[str]

    @classmethod
    def from_domain(cls, assessment: BusinessQualityAssessment) -> "BusinessQualityAssessmentView":
        return cls(
            moat=MoatAssessmentView.from_domain(assessment.moat),
            management=ManagementAssessmentView.from_domain(assessment.management),
            reinvestment=ReinvestmentAssessmentView.from_domain(assessment.reinvestment),
            overall_level=assessment.overall_level.value,
            strengths=[BusinessQualityDriverView.from_domain(d) for d in assessment.strengths],
            weaknesses=[BusinessQualityDriverView.from_domain(d) for d in assessment.weaknesses],
            greatest_advantage=(
                BusinessQualityDriverView.from_domain(assessment.greatest_advantage)
                if assessment.greatest_advantage is not None
                else None
            ),
            greatest_concern=(
                BusinessQualityDriverView.from_domain(assessment.greatest_concern)
                if assessment.greatest_concern is not None
                else None
            ),
            unknowns=list(assessment.unknowns),
        )
