"""HTTP response schemas for the Monitoring API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module. Every field is a direct read of an already-
computed `MonitoringResult`/`MonitoringChange` -- nothing is
recomputed or reworded here.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.monitoring.models import (
    CaseOperationalFreshness,
    MonitoringChange,
    MonitoringFailure,
    MonitoringOperationalStatus,
    MonitoringResult,
    MonitoringRun,
    ScopeFreshnessSummary,
)
from atlas.core.infrastructure.api.serialization import CamelModel


class MonitoringChangeView(CamelModel):
    id: str
    category: str
    materiality: str
    direction: str
    reason: str
    source_capability: str
    evidence_reference: str | None

    @classmethod
    def from_domain(cls, change: MonitoringChange) -> "MonitoringChangeView":
        return cls(
            id=change.id,
            category=change.category.value,
            materiality=change.materiality.value,
            direction=change.direction.value,
            reason=change.reason,
            source_capability=change.source_capability,
            evidence_reference=change.evidence_reference,
        )


class MonitoringResultView(CamelModel):
    case_id: str
    ticker: str | None
    scope: str
    status: str
    changes: list[MonitoringChangeView]
    stance_level: str | None
    confidence_level: str | None
    coverage_level: str | None
    latest_meaningful_evidence_at: datetime | None
    recommended_action: str | None
    generated_at: datetime

    @classmethod
    def from_domain(cls, result: MonitoringResult) -> "MonitoringResultView":
        return cls(
            case_id=result.case_id,
            ticker=result.ticker,
            scope=result.scope.value,
            status=result.status.value,
            changes=[MonitoringChangeView.from_domain(c) for c in result.changes],
            stance_level=result.stance_level,
            confidence_level=result.confidence_level,
            coverage_level=result.coverage_level,
            latest_meaningful_evidence_at=result.latest_meaningful_evidence_at,
            recommended_action=result.recommended_action.value if result.recommended_action is not None else None,
            generated_at=result.generated_at,
        )


class MonitoringRunView(CamelModel):
    generated_at: datetime
    results: list[MonitoringResultView]

    @classmethod
    def from_domain(cls, run: MonitoringRun) -> "MonitoringRunView":
        return cls(generated_at=run.generated_at, results=[MonitoringResultView.from_domain(r) for r in run.results])


class MonitoringFailureView(CamelModel):
    case_id: str
    ticker: str | None
    error: str

    @classmethod
    def from_domain(cls, failure: MonitoringFailure) -> "MonitoringFailureView":
        return cls(case_id=failure.case_id, ticker=failure.ticker, error=failure.error)


class PendingCaseView(CamelModel):
    case_id: str
    ticker: str | None


class ScopeFreshnessSummaryView(CamelModel):
    """Sprint 9, Deliverable 8/9 -- see `ScopeFreshnessSummary`'s own
    docstring for why these three buckets and not a five-way
    breakdown of `DataFreshnessStatus`."""

    waiting_for_analysis: int
    no_new_data: int
    needs_attention: int

    @classmethod
    def from_domain(cls, summary: ScopeFreshnessSummary) -> "ScopeFreshnessSummaryView":
        return cls(
            waiting_for_analysis=summary.waiting_for_analysis,
            no_new_data=summary.no_new_data,
            needs_attention=summary.needs_attention,
        )


class MonitoringOperationalStatusView(CamelModel):
    """Atlas Intelligence Sprint 8, Deliverable 7/14 -- operational
    status only, deliberately shaped nothing like `MonitoringResultView`
    (investment status), so the two can never be confused at the wire
    level either."""

    status: str
    last_run_started_at: datetime | None
    last_run_completed_at: datetime | None
    pending_cases: list[PendingCaseView]
    failed_cases: list[MonitoringFailureView]
    portfolio_freshness: ScopeFreshnessSummaryView
    watchlist_freshness: ScopeFreshnessSummaryView

    @classmethod
    def from_domain(cls, operational_status: MonitoringOperationalStatus) -> "MonitoringOperationalStatusView":
        return cls(
            status=operational_status.status.value,
            last_run_started_at=operational_status.last_run_started_at,
            last_run_completed_at=operational_status.last_run_completed_at,
            pending_cases=[PendingCaseView(case_id=c, ticker=t) for c, t in operational_status.pending_cases],
            failed_cases=[MonitoringFailureView.from_domain(f) for f in operational_status.failed_cases],
            portfolio_freshness=ScopeFreshnessSummaryView.from_domain(operational_status.portfolio_freshness),
            watchlist_freshness=ScopeFreshnessSummaryView.from_domain(operational_status.watchlist_freshness),
        )


class CaseOperationalFreshnessView(CamelModel):
    """Deliverable 15 -- the compact, operational-only fact Investment
    Case exposes alongside (never merged with) `MonitoringStatusView`."""

    is_pending: bool
    last_monitored_at: datetime | None
    last_run_failed_for_case: bool
    data_freshness_status: str
    """Sprint 9 -- one of `waiting_for_new_data`/`waiting_for_analysis`/
    `monitoring_failed`/`no_data_source`/`unknown`."""

    @classmethod
    def from_domain(cls, freshness: CaseOperationalFreshness) -> "CaseOperationalFreshnessView":
        return cls(
            is_pending=freshness.is_pending,
            last_monitored_at=freshness.last_monitored_at,
            last_run_failed_for_case=freshness.last_run_failed_for_case,
            data_freshness_status=freshness.data_freshness_status.value,
        )
