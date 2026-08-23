"""HTTP response schemas for the Materiality API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module.
"""
from __future__ import annotations

from atlas.alpha.coverage import DimensionCoverage
from atlas.alpha.materiality.models import MaterialEvidence, MaterialityAssessment
from atlas.alpha.stance import StanceReason
from atlas.core.infrastructure.api.serialization import CamelModel


class StanceReasonView(CamelModel):
    """Independently declared here, field-for-field identical to every
    other Alpha package's own `StanceReasonView` -- this codebase's own
    no-cross-package-View-import convention."""

    code: str

    @classmethod
    def from_domain(cls, reason: StanceReason) -> "StanceReasonView":
        return cls(code=reason.code.value)


class DimensionCoverageView(CamelModel):
    dimension: str
    level: str
    reasoning: list[str]

    @classmethod
    def from_domain(cls, coverage: DimensionCoverage) -> "DimensionCoverageView":
        return cls(dimension=coverage.dimension, level=coverage.level.value, reasoning=list(coverage.reasoning))


class MaterialEvidenceView(CamelModel):
    reason: StanceReasonView
    materiality: str

    @classmethod
    def from_domain(cls, item: MaterialEvidence) -> "MaterialEvidenceView":
        return cls(reason=StanceReasonView.from_domain(item.reason), materiality=item.materiality.value)


class MaterialityAssessmentView(CamelModel):
    supporting_evidence: list[MaterialEvidenceView]
    contradicting_evidence: list[MaterialEvidenceView]
    limiting_factors: list[MaterialEvidenceView]
    top_supporting_evidence: MaterialEvidenceView | None
    top_contradicting_evidence: MaterialEvidenceView | None
    top_limiting_factor: MaterialEvidenceView | None
    top_missing_evidence: DimensionCoverageView | None

    @classmethod
    def from_domain(cls, assessment: MaterialityAssessment) -> "MaterialityAssessmentView":
        return cls(
            supporting_evidence=[MaterialEvidenceView.from_domain(i) for i in assessment.supporting_evidence],
            contradicting_evidence=[MaterialEvidenceView.from_domain(i) for i in assessment.contradicting_evidence],
            limiting_factors=[MaterialEvidenceView.from_domain(i) for i in assessment.limiting_factors],
            top_supporting_evidence=(
                MaterialEvidenceView.from_domain(assessment.top_supporting_evidence)
                if assessment.top_supporting_evidence is not None
                else None
            ),
            top_contradicting_evidence=(
                MaterialEvidenceView.from_domain(assessment.top_contradicting_evidence)
                if assessment.top_contradicting_evidence is not None
                else None
            ),
            top_limiting_factor=(
                MaterialEvidenceView.from_domain(assessment.top_limiting_factor)
                if assessment.top_limiting_factor is not None
                else None
            ),
            top_missing_evidence=(
                DimensionCoverageView.from_domain(assessment.top_missing_evidence)
                if assessment.top_missing_evidence is not None
                else None
            ),
        )
