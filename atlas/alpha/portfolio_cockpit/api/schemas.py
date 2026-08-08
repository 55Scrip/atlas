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

from atlas.alpha.portfolio_cockpit.models import (
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


class ValuationFindingView(CamelModel):
    kind: str
    status: str
    severity: str
    supporting_facts: list[str]
    contradicting_facts: list[str]
    assumptions: list[str]
    missing_evidence: list[str]
    confidence: str

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


class PortfolioHoldingAnalysisView(CamelModel):
    ticker: str
    case_id: str
    weight_percent: float
    value_absolute: float | None
    reconciliation_status: str
    conviction: ConvictionAssessmentView
    valuation: ValuationFindingView
    business: BusinessSummaryView
    risk_projection: RiskProjectionView
    risk_findings: list[RiskFindingView]
    confidence: str
    is_thesis_stale: bool
    attention: HoldingAttentionView

    @classmethod
    def from_domain(cls, analysis: PortfolioHoldingAnalysis) -> "PortfolioHoldingAnalysisView":
        return cls(
            ticker=analysis.ticker,
            case_id=analysis.case_id,
            weight_percent=analysis.weight_percent,
            value_absolute=analysis.value_absolute,
            reconciliation_status=analysis.reconciliation_status.value,
            conviction=ConvictionAssessmentView.from_domain(analysis.conviction),
            valuation=ValuationFindingView.from_domain(analysis.valuation),
            business=BusinessSummaryView.from_domain(analysis.business),
            risk_projection=RiskProjectionView.from_domain(analysis.risk_projection),
            risk_findings=[RiskFindingView.from_domain(f) for f in analysis.risk_findings],
            confidence=analysis.confidence.value,
            is_thesis_stale=analysis.is_thesis_stale,
            attention=HoldingAttentionView.from_domain(analysis.attention),
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


class PortfolioCockpitView(CamelModel):
    exists: bool
    holdings: list[PortfolioHoldingAnalysisView]
    unresolved_holdings: list[UnresolvedHoldingView]
    summary: PortfolioSummaryView | None
    conviction_distribution: list[ConvictionLevelCountView]
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
            valuation_distribution=[
                ValuationStatusCountView.from_domain(v) for v in report.valuation_distribution
            ],
            priority_review_count=report.priority_review_count,
            generated_at=report.generated_at,
        )
