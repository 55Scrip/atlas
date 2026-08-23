"""HTTP response schemas for the Explainability API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module.
"""
from __future__ import annotations

from atlas.alpha.coverage import ConfidenceReason, DimensionCoverage
from atlas.alpha.explainability.models import ComparisonEvidence, Explanation
from atlas.alpha.stance import StanceReason
from atlas.core.infrastructure.api.serialization import CamelModel


class StanceReasonView(CamelModel):
    """Independently declared here, field-for-field identical to
    `atlas.alpha.investment_case.api.schemas.StanceReasonView` -- this
    codebase's own no-cross-package-View-import convention."""

    code: str

    @classmethod
    def from_domain(cls, reason: StanceReason) -> "StanceReasonView":
        return cls(code=reason.code.value)


class ConfidenceReasonView(CamelModel):
    code: str
    count: int | None
    total: int | None

    @classmethod
    def from_domain(cls, reason: ConfidenceReason) -> "ConfidenceReasonView":
        return cls(code=reason.code.value, count=reason.count, total=reason.total)


class DimensionCoverageView(CamelModel):
    dimension: str
    level: str
    reasoning: list[str]

    @classmethod
    def from_domain(cls, coverage: DimensionCoverage) -> "DimensionCoverageView":
        return cls(dimension=coverage.dimension, level=coverage.level.value, reasoning=list(coverage.reasoning))


class ExplanationView(CamelModel):
    supporting_evidence: list[StanceReasonView]
    contradicting_evidence: list[StanceReasonView]
    limiting_factors: list[StanceReasonView]
    missing_evidence: list[DimensionCoverageView]
    confidence_drivers: list[ConfidenceReasonView]
    most_valuable_missing_information: DimensionCoverageView | None

    @classmethod
    def from_domain(cls, explanation: Explanation) -> "ExplanationView":
        return cls(
            supporting_evidence=[StanceReasonView.from_domain(r) for r in explanation.supporting_evidence],
            contradicting_evidence=[StanceReasonView.from_domain(r) for r in explanation.contradicting_evidence],
            limiting_factors=[StanceReasonView.from_domain(r) for r in explanation.limiting_factors],
            missing_evidence=[DimensionCoverageView.from_domain(d) for d in explanation.missing_evidence],
            confidence_drivers=[ConfidenceReasonView.from_domain(r) for r in explanation.confidence_drivers],
            most_valuable_missing_information=(
                DimensionCoverageView.from_domain(explanation.most_valuable_missing_information)
                if explanation.most_valuable_missing_information is not None
                else None
            ),
        )


class ComparisonEvidenceView(CamelModel):
    favoring_a: list[StanceReasonView]
    favoring_b: list[StanceReasonView]
    shared: list[StanceReasonView]
    missing_for_both: list[str]

    @classmethod
    def from_domain(cls, comparison: ComparisonEvidence) -> "ComparisonEvidenceView":
        return cls(
            favoring_a=[StanceReasonView.from_domain(r) for r in comparison.favoring_a],
            favoring_b=[StanceReasonView.from_domain(r) for r in comparison.favoring_b],
            shared=[StanceReasonView.from_domain(r) for r in comparison.shared],
            missing_for_both=list(comparison.missing_for_both),
        )
