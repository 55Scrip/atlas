"""Orchestration for Data Ingestion & Automatic Refresh (Deliverable 3).
The only part of this package that performs I/O -- composes
`atlas.alpha.business_data_refresh.refresh_company_data`/
`ensure_company_enriched` unmodified (Sprint 9 adds one new,
already-defaulted field to their own `RefreshSummary`, never new
fetch/validate/version logic of its own -- see that package's own
`models.py`), classifies the result via this package's own pure
`engine.classify_refresh`, and persists it as the Case's latest
`IngestionResult`.

**One canonical ingestion path.** `IngestionService.refresh()` always
calls `refresh_company_data` (a real, forced check against every
provider); `.ensure_enriched_and_record()` wraps the existing lazy/
idempotent `ensure_company_enriched` trigger Portfolio/Watchlist
already use. Both funnel through the identical `_record()` helper --
there is no second, parallel classification path.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched, refresh_company_data
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.ingestion.engine import classify_refresh
from atlas.alpha.ingestion.models import IngestionResult
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.analysis_engine.business_data.providers import BusinessDataProvider

__all__ = ["IngestionService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IngestionService:
    def __init__(
        self,
        providers: tuple[BusinessDataProvider, ...],
        business_record_repository: SqlAlchemyBusinessRecordRepository,
        identity_gate: CanonicalSecurityIdentityGate,
        ingestion_result_repository: SqlAlchemyIngestionResultRepository,
    ) -> None:
        self._providers = providers
        self._business_record_repository = business_record_repository
        self._identity_gate = identity_gate
        self._ingestion_result_repository = ingestion_result_repository

    def _record(self, ticker: str, case_id: str | None, summary) -> IngestionResult:
        ran_at = summary.evaluated_at or _utc_now()
        result = classify_refresh(summary, ticker=ticker, case_id=case_id, ran_at=ran_at)
        self._ingestion_result_repository.upsert(result)
        return result

    def refresh(self, ticker: str, case_id: str | None) -> IngestionResult:
        """Deliverable 16's own explicit operation -- always calls
        every provider, regardless of whether `ticker` already looks
        minimally complete. This is the one way to genuinely force a
        fresh check (mirrors `atlas.alpha.monitoring.service
        .MonitoringService.run`'s own `force=True` escape hatch)."""
        summary = refresh_company_data(ticker, self._providers, self._business_record_repository, identity_gate=self._identity_gate)
        return self._record(ticker, case_id, summary)

    def ensure_enriched_and_record(self, ticker: str, case_id: str | None) -> IngestionResult | None:
        """Wraps the existing lazy/idempotent `ensure_company_enriched`
        trigger. `None` when it no-ops (already minimally complete) --
        an honest "no check happened," never a fabricated "nothing
        new" `IngestionResult`; the Case's prior `IngestionResult` (if
        any) is left exactly as it was."""
        summary = ensure_company_enriched(ticker, self._providers, self._business_record_repository, identity_gate=self._identity_gate)
        if summary is None:
            return None
        return self._record(ticker, case_id, summary)

    def get_latest(self, case_id: str) -> IngestionResult | None:
        return self._ingestion_result_repository.get(case_id)
