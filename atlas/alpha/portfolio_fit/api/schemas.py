"""HTTP response schemas for the Portfolio Fit API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module. Every enum is sent as its `.value` string --
the frontend owns localized labels via its own key map, the same
convention every other categorical field in this codebase already
follows (see `frontend/src/status/statusTone.ts`'s own module docstring).
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.coverage import CoverageAssessment, DimensionCoverage
from atlas.alpha.coverage.models import ConfidenceReason
from atlas.alpha.portfolio_fit.models import FitComparison, FitDimension, PortfolioFitAssessment
from atlas.core.infrastructure.api.serialization import CamelModel


class DimensionCoverageView(CamelModel):
    """Atlas Intelligence Sprint 1. Independently declared here, field-
    for-field identical to the equivalent view in
    `atlas.alpha.investment_case.api.schemas`/
    `atlas.alpha.portfolio_cockpit.api.schemas` -- this codebase's own
    no-cross-package-View-import convention."""

    dimension: str
    level: str
    reasoning: list[str]

    @classmethod
    def from_domain(cls, coverage: DimensionCoverage) -> "DimensionCoverageView":
        return cls(dimension=coverage.dimension, level=coverage.level.value, reasoning=list(coverage.reasoning))


class ConfidenceReasonView(CamelModel):
    """Atlas Intelligence Sprint 1. Independently declared here, field-
    for-field identical to the equivalent view in
    `atlas.alpha.investment_case.api.schemas`/
    `atlas.alpha.portfolio_cockpit.api.schemas` -- this module's own
    no-cross-package-View-import convention."""

    code: str
    count: int | None
    total: int | None

    @classmethod
    def from_domain(cls, reason: ConfidenceReason) -> "ConfidenceReasonView":
        return cls(code=reason.code.value, count=reason.count, total=reason.total)


class CoverageAssessmentView(CamelModel):
    dimensions: list[DimensionCoverageView]
    overall_coverage: str
    overall_confidence: str
    missing_dimensions: list[str]
    not_applicable_dimensions: list[str]
    reasoning: list[ConfidenceReasonView]

    @classmethod
    def from_domain(cls, assessment: CoverageAssessment) -> "CoverageAssessmentView":
        return cls(
            dimensions=[DimensionCoverageView.from_domain(d) for d in assessment.dimensions],
            overall_coverage=assessment.overall_coverage.value,
            overall_confidence=assessment.overall_confidence.value,
            missing_dimensions=list(assessment.missing_dimensions),
            not_applicable_dimensions=list(assessment.not_applicable_dimensions),
            reasoning=[ConfidenceReasonView.from_domain(r) for r in assessment.reasoning],
        )


class FitDimensionView(CamelModel):
    kind: str
    rating: str
    reasoning: list[str]
    unavailable_reason: str | None

    @classmethod
    def from_domain(cls, dimension: FitDimension) -> "FitDimensionView":
        return cls(
            kind=dimension.kind.value,
            rating=dimension.rating.value,
            reasoning=list(dimension.reasoning),
            unavailable_reason=dimension.unavailable_reason,
        )


class PortfolioFitAssessmentView(CamelModel):
    case_id: str
    ticker: str
    is_existing_holding: bool
    current_weight_percent: float | None
    overall: str
    overall_reasoning: list[str]
    dimensions: list[FitDimensionView]
    trend: str
    data_gaps: list[str]
    coverage: CoverageAssessmentView
    generated_at: datetime

    @classmethod
    def from_domain(cls, assessment: PortfolioFitAssessment) -> "PortfolioFitAssessmentView":
        return cls(
            case_id=assessment.case_id,
            ticker=assessment.ticker,
            is_existing_holding=assessment.is_existing_holding,
            current_weight_percent=assessment.current_weight_percent,
            overall=assessment.overall.value,
            overall_reasoning=list(assessment.overall_reasoning),
            dimensions=[FitDimensionView.from_domain(d) for d in assessment.dimensions],
            trend=assessment.trend.value,
            data_gaps=list(assessment.data_gaps),
            coverage=CoverageAssessmentView.from_domain(assessment.coverage),
            generated_at=assessment.generated_at,
        )


class FitComparisonView(CamelModel):
    assessment_a: PortfolioFitAssessmentView
    assessment_b: PortfolioFitAssessmentView
    preferred_ticker: str | None
    reasoning: list[str]

    @classmethod
    def from_domain(cls, comparison: FitComparison) -> "FitComparisonView":
        return cls(
            assessment_a=PortfolioFitAssessmentView.from_domain(comparison.assessment_a),
            assessment_b=PortfolioFitAssessmentView.from_domain(comparison.assessment_b),
            preferred_ticker=comparison.preferred_ticker,
            reasoning=list(comparison.reasoning),
        )
