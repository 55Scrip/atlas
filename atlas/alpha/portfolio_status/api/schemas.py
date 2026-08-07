"""HTTP response schemas for the Portfolio Status API (ATLAS-015).

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
reused exactly like `atlas/alpha/portfolio/api/schemas.py` does. Every
field name here mirrors its domain source verbatim -- no field is
renamed for presentation, matching the `decisionType`/`transactionType`
precedent (raw English values, translated only at display time by the
frontend).
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.portfolio_status.models import (
    AttentionItem,
    PortfolioHealthMetrics,
    PortfolioStatusReport,
    PortfolioSummaryMetrics,
    ReviewQueueItem,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class PortfolioSummaryView(CamelModel):
    holdings_count: int
    largest_position_ticker: str | None
    largest_position_weight_percent: float | None
    number_of_investment_cases: int
    open_decisions: int
    pending_outcomes: int
    pending_executions: int
    concentration_level: str | None
    unallocated_percent: float | None

    @classmethod
    def from_domain(cls, metrics: PortfolioSummaryMetrics) -> "PortfolioSummaryView":
        return cls(
            holdings_count=metrics.holdings_count,
            largest_position_ticker=metrics.largest_position_ticker,
            largest_position_weight_percent=metrics.largest_position_weight_percent,
            number_of_investment_cases=metrics.number_of_investment_cases,
            open_decisions=metrics.open_decisions,
            pending_outcomes=metrics.pending_outcomes,
            pending_executions=metrics.pending_executions,
            concentration_level=metrics.concentration_level,
            unallocated_percent=metrics.unallocated_percent,
        )


class AttentionItemView(CamelModel):
    ticker: str
    category: str
    case_id: str | None
    age_days: int | None

    @classmethod
    def from_domain(cls, item: AttentionItem) -> "AttentionItemView":
        return cls(
            ticker=item.ticker,
            category=item.category.value,
            case_id=item.case_id,
            age_days=item.age_days,
        )


class ReviewQueueItemView(CamelModel):
    ticker: str
    case_id: str | None
    reason_count: int
    top_category: str

    @classmethod
    def from_domain(cls, item: ReviewQueueItem) -> "ReviewQueueItemView":
        return cls(
            ticker=item.ticker,
            case_id=item.case_id,
            reason_count=item.reason_count,
            top_category=item.top_category.value,
        )


class PortfolioHealthView(CamelModel):
    holdings_with_case_count: int
    holdings_count: int
    most_recent_decision_at: datetime | None
    outstanding_workflow_items: int
    allocated_percent: float | None
    unknown_instrument_tickers: list[str]

    @classmethod
    def from_domain(cls, metrics: PortfolioHealthMetrics) -> "PortfolioHealthView":
        return cls(
            holdings_with_case_count=metrics.holdings_with_case_count,
            holdings_count=metrics.holdings_count,
            most_recent_decision_at=metrics.most_recent_decision_at,
            outstanding_workflow_items=metrics.outstanding_workflow_items,
            allocated_percent=metrics.allocated_percent,
            unknown_instrument_tickers=list(metrics.unknown_instrument_tickers),
        )


class PortfolioStatusView(CamelModel):
    exists: bool
    summary: PortfolioSummaryView | None
    attention_items: list[AttentionItemView]
    review_queue: list[ReviewQueueItemView]
    health: PortfolioHealthView | None

    @classmethod
    def from_domain(cls, report: PortfolioStatusReport) -> "PortfolioStatusView":
        return cls(
            exists=report.exists,
            summary=PortfolioSummaryView.from_domain(report.summary) if report.summary else None,
            attention_items=[AttentionItemView.from_domain(item) for item in report.attention_items],
            review_queue=[ReviewQueueItemView.from_domain(item) for item in report.review_queue],
            health=PortfolioHealthView.from_domain(report.health) if report.health else None,
        )
