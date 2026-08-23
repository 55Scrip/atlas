"""HTTP response schemas for the Portfolio Cockpit API (ATLAS-028).

Wire format is camelCase via the shared Core `CamelModel` (ADR-004).
Every enum is serialized as its raw English `.value`, matching every
prior Alpha schema module. `summary` reuses `PortfolioSummaryView`
directly from `atlas.alpha.portfolio_status.api.schemas` -- the same
wire shape, never redefined.

`Provenance` is deliberately not serialized anywhere in this module,
matching the precedent already set by `case_intelligence`'s own schema
(which never exposes it either): it is Investment-Case-depth plumbing,
not Portfolio-Cockpit-overview content. Per this sprint's own "Portfolio
is overview, Investment Case is depth" principle, a holding row here
carries only what the Investment Case's own `case_id` can't already give
you one click away.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.decision_support import DecisionSupportView as DecisionSupportViewDomain
from atlas.alpha.portfolio_cockpit.models import (
    AnalysisCoverageLevelCount,
    BusinessSummary,
    ConvictionLevelCount,
    HoldingAttention,
    PortfolioCockpitReport,
    PortfolioHoldingAnalysis,
    RiskProjection,
    UnresolvedHolding,
    ValuationStatusCount,
)
from atlas.alpha.portfolio_status.api.schemas import PortfolioSummaryView
from atlas.alpha.coverage import CoverageAssessment, DimensionCoverage
from atlas.alpha.coverage.models import ConfidenceReason
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageAssessment
from atlas.analysis_engine.conviction import ConvictionAssessment
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.analysis_engine.valuation.models import ValuationFinding
from atlas.core.infrastructure.api.serialization import CamelModel


class ConvictionAssessmentView(CamelModel):
    level: str
    reasons: list[str]

    @classmethod
    def from_domain(cls, assessment: ConvictionAssessment) -> "ConvictionAssessmentView":
        return cls(level=assessment.level.value, reasons=[r.value for r in assessment.reasons])


class AnalysisCoverageAssessmentView(CamelModel):
    level: str
    reasons: list[str]

    @classmethod
    def from_domain(cls, assessment: AnalysisCoverageAssessment) -> "AnalysisCoverageAssessmentView":
        return cls(level=assessment.level.value, reasons=[r.value for r in assessment.reasons])


class DimensionCoverageView(CamelModel):
    """Atlas Intelligence Sprint 1. Independently declared here, field-
    for-field identical to `atlas.alpha.investment_case.api.schemas
    .DimensionCoverageView` -- this module's own no-cross-package-
    View-import convention, matching `ConvictionAssessmentView`/
    `AnalysisCoverageAssessmentView` above."""

    dimension: str
    level: str
    reasoning: list[str]

    @classmethod
    def from_domain(cls, coverage: DimensionCoverage) -> "DimensionCoverageView":
        return cls(dimension=coverage.dimension, level=coverage.level.value, reasoning=list(coverage.reasoning))


class ConfidenceReasonView(CamelModel):
    """Atlas Intelligence Sprint 1. Independently declared here, field-
    for-field identical to the equivalent view in
    `atlas.alpha.investment_case.api.schemas` -- this module's own
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


class ValuationFindingView(CamelModel):
    kind: str
    status: str
    severity: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    assumptions: list[str]
    missing_evidence: list[str]
    confidence: str
    current_yield: float | None

    @classmethod
    def from_domain(cls, finding: ValuationFinding) -> "ValuationFindingView":
        return cls(
            kind=finding.kind.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_facts=list(finding.supporting_facts),
            contradicting_facts=list(finding.contradicting_facts),
            assumptions=[a.value for a in finding.assumptions],
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
            current_yield=finding.current_yield,
        )


class RiskFindingView(CamelModel):
    category: str
    status: str
    severity: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    missing_evidence: list[str]
    confidence: str

    @classmethod
    def from_domain(cls, finding: RiskFinding) -> "RiskFindingView":
        return cls(
            category=finding.category.value,
            status=finding.status.value,
            severity=finding.severity.value,
            supporting_facts=list(finding.supporting_facts),
            contradicting_facts=list(finding.contradicting_facts),
            missing_evidence=[m.value for m in finding.missing_evidence],
            confidence=finding.confidence.value,
        )


class RiskProjectionView(CamelModel):
    category: str
    status: str

    @classmethod
    def from_domain(cls, projection: RiskProjection) -> "RiskProjectionView":
        return cls(category=projection.category.value, status=projection.status.value)


class BusinessSummaryView(CamelModel):
    growth: str
    capital_allocation: str

    @classmethod
    def from_domain(cls, summary: BusinessSummary) -> "BusinessSummaryView":
        return cls(growth=summary.growth.value, capital_allocation=summary.capital_allocation.value)


class HoldingAttentionView(CamelModel):
    priority: str
    reasons: list[str]

    @classmethod
    def from_domain(cls, attention: HoldingAttention) -> "HoldingAttentionView":
        return cls(priority=attention.priority.value, reasons=[r.value for r in attention.reasons])


class DecisionSupportView(CamelModel):
    """Migration Review §11.1's Holdings-table Action column --
    evidence-support language only, never a raw `RecommendationDirection`
    member name. See `atlas.alpha.decision_support`'s own module
    docstring."""

    level: str
    badge_label: str
    statement: str

    @classmethod
    def from_domain(cls, view: DecisionSupportViewDomain) -> "DecisionSupportView":
        return cls(level=view.level.value, badge_label=view.badge_label, statement=view.statement)


class PortfolioHoldingAnalysisView(CamelModel):
    ticker: str
    case_id: str
    weight_percent: float
    value_absolute: float | None
    reconciliation_status: str
    conviction: ConvictionAssessmentView
    analysis_coverage: AnalysisCoverageAssessmentView
    valuation: ValuationFindingView
    business: BusinessSummaryView
    risk_projection: RiskProjectionView
    risk_findings: list[RiskFindingView]
    confidence: str
    is_thesis_stale: bool
    attention: HoldingAttentionView
    decision_support: DecisionSupportView
    coverage: CoverageAssessmentView

    @classmethod
    def from_domain(cls, analysis: PortfolioHoldingAnalysis) -> "PortfolioHoldingAnalysisView":
        return cls(
            ticker=analysis.ticker,
            case_id=analysis.case_id,
            weight_percent=analysis.weight_percent,
            value_absolute=analysis.value_absolute,
            reconciliation_status=analysis.reconciliation_status.value,
            conviction=ConvictionAssessmentView.from_domain(analysis.conviction),
            analysis_coverage=AnalysisCoverageAssessmentView.from_domain(analysis.analysis_coverage),
            valuation=ValuationFindingView.from_domain(analysis.valuation),
            business=BusinessSummaryView.from_domain(analysis.business),
            risk_projection=RiskProjectionView.from_domain(analysis.risk_projection),
            risk_findings=[RiskFindingView.from_domain(f) for f in analysis.risk_findings],
            confidence=analysis.confidence.value,
            is_thesis_stale=analysis.is_thesis_stale,
            attention=HoldingAttentionView.from_domain(analysis.attention),
            decision_support=DecisionSupportView.from_domain(analysis.decision_support),
            coverage=CoverageAssessmentView.from_domain(analysis.coverage),
        )


class UnresolvedHoldingView(CamelModel):
    ticker: str
    case_id: str | None

    @classmethod
    def from_domain(cls, holding: UnresolvedHolding) -> "UnresolvedHoldingView":
        return cls(ticker=holding.ticker, case_id=holding.case_id)


class ConvictionLevelCountView(CamelModel):
    level: str
    count: int

    @classmethod
    def from_domain(cls, entry: ConvictionLevelCount) -> "ConvictionLevelCountView":
        return cls(level=entry.level.value, count=entry.count)


class ValuationStatusCountView(CamelModel):
    status: str
    count: int

    @classmethod
    def from_domain(cls, entry: ValuationStatusCount) -> "ValuationStatusCountView":
        return cls(status=entry.status.value, count=entry.count)


class AnalysisCoverageLevelCountView(CamelModel):
    level: str
    count: int

    @classmethod
    def from_domain(cls, entry: AnalysisCoverageLevelCount) -> "AnalysisCoverageLevelCountView":
        return cls(level=entry.level.value, count=entry.count)


class PortfolioCockpitView(CamelModel):
    exists: bool
    holdings: list[PortfolioHoldingAnalysisView]
    unresolved_holdings: list[UnresolvedHoldingView]
    summary: PortfolioSummaryView | None
    conviction_distribution: list[ConvictionLevelCountView]
    analysis_coverage_distribution: list[AnalysisCoverageLevelCountView]
    valuation_distribution: list[ValuationStatusCountView]
    priority_review_count: int
    generated_at: datetime

    @classmethod
    def from_domain(cls, report: PortfolioCockpitReport) -> "PortfolioCockpitView":
        return cls(
            exists=report.exists,
            holdings=[PortfolioHoldingAnalysisView.from_domain(h) for h in report.holdings],
            unresolved_holdings=[UnresolvedHoldingView.from_domain(u) for u in report.unresolved_holdings],
            summary=PortfolioSummaryView.from_domain(report.summary) if report.summary else None,
            conviction_distribution=[
                ConvictionLevelCountView.from_domain(c) for c in report.conviction_distribution
            ],
            analysis_coverage_distribution=[
                AnalysisCoverageLevelCountView.from_domain(c) for c in report.analysis_coverage_distribution
            ],
            valuation_distribution=[
                ValuationStatusCountView.from_domain(v) for v in report.valuation_distribution
            ],
            priority_review_count=report.priority_review_count,
            generated_at=report.generated_at,
        )
