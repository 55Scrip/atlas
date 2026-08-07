"""HTTP response schemas for the Portfolio Intelligence API (ATLAS-016).

Wire format is camelCase via the shared Core `CamelModel` (ADR-004).
Every enum is serialized as its raw English `.value` -- the same
"translated only at display time by the frontend" pattern
`decisionType`/`transactionType`/`category` already use elsewhere.
`overview` reuses `PortfolioStatusApi`'s own `PortfolioSummaryView`
shape directly rather than duplicating field definitions.
"""
from __future__ import annotations

from atlas.alpha.portfolio_intelligence.models import (
    ConsiderItem,
    KeyFinding,
    MissingEvidenceItem,
    PortfolioFitStatus,
    PortfolioIntelligenceReport,
    RiskSignal,
)
from atlas.alpha.portfolio_status.api.schemas import PortfolioSummaryView
from atlas.core.infrastructure.api.serialization import CamelModel


class KeyFindingView(CamelModel):
    kind: str
    count: int
    tickers: list[str]

    @classmethod
    def from_domain(cls, finding: KeyFinding) -> "KeyFindingView":
        return cls(kind=finding.kind.value, count=finding.count, tickers=list(finding.tickers))


class ConsiderItemView(CamelModel):
    kind: str
    ticker: str
    case_id: str | None
    confidence: str
    related_holdings: list[str]
    evidence_gap_count: int | None
    age_days: int | None
    weight_percent: float | None
    pending_item_count: int | None

    @classmethod
    def from_domain(cls, item: ConsiderItem) -> "ConsiderItemView":
        return cls(
            kind=item.kind.value,
            ticker=item.ticker,
            case_id=item.case_id,
            confidence=item.confidence.value,
            related_holdings=list(item.related_holdings),
            evidence_gap_count=item.evidence_gap_count,
            age_days=item.age_days,
            weight_percent=item.weight_percent,
            pending_item_count=item.pending_item_count,
        )


class RiskSignalView(CamelModel):
    kind: str
    ticker: str
    case_id: str | None
    age_days: int | None

    @classmethod
    def from_domain(cls, signal: RiskSignal) -> "RiskSignalView":
        return cls(
            kind=signal.kind.value, ticker=signal.ticker, case_id=signal.case_id, age_days=signal.age_days
        )


class MissingEvidenceItemView(CamelModel):
    ticker: str
    case_id: str
    gap_kind: str
    reference: str | None

    @classmethod
    def from_domain(cls, item: MissingEvidenceItem) -> "MissingEvidenceItemView":
        return cls(
            ticker=item.ticker, case_id=item.case_id, gap_kind=item.gap_kind.value, reference=item.reference
        )


class PortfolioFitStatusView(CamelModel):
    available: bool
    reason: str | None

    @classmethod
    def from_domain(cls, status: PortfolioFitStatus) -> "PortfolioFitStatusView":
        return cls(available=status.available, reason=status.reason.value if status.reason else None)


class PortfolioIntelligenceView(CamelModel):
    exists: bool
    overview: PortfolioSummaryView | None
    cash_weight_percent: float | None
    cash_value_absolute: float | None
    key_findings: list[KeyFindingView]
    consider_items: list[ConsiderItemView]
    risk_signals: list[RiskSignalView]
    missing_evidence: list[MissingEvidenceItemView]
    portfolio_fit: PortfolioFitStatusView

    @classmethod
    def from_domain(cls, report: PortfolioIntelligenceReport) -> "PortfolioIntelligenceView":
        return cls(
            exists=report.exists,
            overview=PortfolioSummaryView.from_domain(report.overview) if report.overview else None,
            cash_weight_percent=report.cash_weight_percent,
            cash_value_absolute=report.cash_value_absolute,
            key_findings=[KeyFindingView.from_domain(f) for f in report.key_findings],
            consider_items=[ConsiderItemView.from_domain(c) for c in report.consider_items],
            risk_signals=[RiskSignalView.from_domain(s) for s in report.risk_signals],
            missing_evidence=[MissingEvidenceItemView.from_domain(m) for m in report.missing_evidence],
            portfolio_fit=PortfolioFitStatusView.from_domain(report.portfolio_fit),
        )
