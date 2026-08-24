"""Price-only refresh orchestration (Internal Alpha Stabilization 1,
MSFT price root cause fix).

The one place `AlphaVantageMarketDataProvider.fetch_price_only` is
ever called. Deliberately small: no persistent job queue, no
scheduler -- a single process-wide `PriceRefreshCoordinator` (in-
memory, reset on restart, which is safe: it only ever *dedupes and
serializes in-flight work*, it never decides what's allowed today,
which is the persisted `AlphaVantageQuotaTracker`'s job) plus one
function that does the actual refresh.

Never sweeps a portfolio or watchlist. The only caller is the
Investment Case analysis endpoint, for the one ticker a user is
actually looking at right now (lazy, on view) -- or the manual
"Uppdatera" action, which calls the identical function.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal

from atlas.analysis_engine.business_data.freshness import is_price_fresh
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.pipeline import IngestedRecord, ingest
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.errors import BusinessDataProviderError

__all__ = ["PriceRefreshCoordinator", "PriceFreshnessStatus", "refresh_price_only", "price_freshness_status"]

PriceFreshnessStatus = Literal["fresh", "stale", "refreshing", "failed", "unavailable"]


class PriceRefreshCoordinator:
    """Process-wide (one instance, constructed once at app startup and
    reused across requests via FastAPI's own `Depends()` caching --
    see `api/dependencies.py`). Two jobs, both in-memory by design:

    1. Dedup + global serialization: `try_start`/`finish` guarantee at
       most one Alpha Vantage price refresh is ever in flight at a
       time, process-wide (never per-ticker only -- the real burst
       limit is shared across every ticker), and a second request for
       a ticker already refreshing is a no-op, never a second call.
    2. `refreshing`/`failed` status for the UI -- purely informational,
       never affects what data is actually shown (the underlying
       `BusinessRecord` is untouched either way). Resetting on restart
       is safe: a ticker just reads as plain "stale" again until its
       next real attempt, never a wrong or stuck status.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._in_flight: set[str] = set()
        self._last_failed: set[str] = set()

    def is_refreshing(self, ticker: str) -> bool:
        with self._lock:
            return ticker in self._in_flight

    def try_start(self, ticker: str) -> bool:
        """`True` if this call actually claimed the ticker (caller
        should proceed); `False` if it was already in flight (caller
        must do nothing -- this *is* the dedup)."""
        with self._lock:
            if ticker in self._in_flight:
                return False
            self._in_flight.add(ticker)
            self._last_failed.discard(ticker)
            return True

    def finish(self, ticker: str, *, succeeded: bool) -> None:
        with self._lock:
            self._in_flight.discard(ticker)
            if succeeded:
                self._last_failed.discard(ticker)
            else:
                self._last_failed.add(ticker)

    def has_recently_failed(self, ticker: str) -> bool:
        with self._lock:
            return ticker in self._last_failed


def _latest_market_snapshot_record(records: tuple[BusinessRecord, ...]) -> BusinessRecord | None:
    snapshots = [r for r in records if r.document_type is SourceKind.MARKET_DATA_SNAPSHOT]
    if not snapshots:
        return None
    return max(snapshots, key=lambda r: r.published_at)


def price_freshness_status(
    *,
    trading_day: date | None,
    ticker: str,
    coordinator: PriceRefreshCoordinator,
    as_of: datetime | None = None,
) -> PriceFreshnessStatus:
    """The one place `refreshing`/`failed` (coordinator state) and
    `fresh`/`stale`/`unavailable` (the pure freshness rule) are
    combined into the single status the UI shows. `refreshing` always
    wins (it is the most current, most specific fact); `failed` only
    matters while the underlying data is still stale (a recent failure
    against an otherwise-fresh price -- e.g. a fresh price fetched by
    someone else in between -- is stale information itself and is not
    shown)."""
    if coordinator.is_refreshing(ticker):
        return "refreshing"
    if trading_day is None:
        return "unavailable"
    fresh = is_price_fresh(trading_day, as_of=as_of or datetime.now(timezone.utc))
    if fresh:
        return "fresh"
    if coordinator.has_recently_failed(ticker):
        return "failed"
    return "stale"


@dataclass(frozen=True)
class PriceRefreshOutcome:
    attempted: bool
    succeeded: bool
    reason: str


def refresh_price_only(
    ticker: str,
    *,
    provider: AlphaVantageMarketDataProvider,
    repository: SqlAlchemyBusinessRecordRepository,
    quota: AlphaVantageQuotaTracker,
    coordinator: PriceRefreshCoordinator,
    evaluated_at: datetime | None = None,
) -> PriceRefreshOutcome:
    """Synchronous by design -- the caller (a FastAPI `BackgroundTasks`
    task, or the manual "Uppdatera" endpoint handler) is already
    running off the request/response path, so no `async`/queue is
    needed for this to not block a page load. Never raises: every real
    failure (rate limit, malformed response, no eligible currency on
    file, no budget left) is reported back as a non-attempted or
    failed `PriceRefreshOutcome`, never an exception the caller has to
    handle -- and, by construction, ingestion only ever happens after
    a fully successful provider response, so a failed attempt never
    writes anything and the last good snapshot is always left exactly
    as it was.
    """
    if not coordinator.try_start(ticker):
        return PriceRefreshOutcome(attempted=False, succeeded=False, reason="already_refreshing")

    succeeded = False
    try:
        if not quota.has_budget():
            return PriceRefreshOutcome(attempted=False, succeeded=False, reason="quota_exhausted")

        existing = repository.get_by_company(ticker)
        latest_snapshot = _latest_market_snapshot_record(existing)
        if latest_snapshot is None:
            # No prior confirmed currency to carry forward -- this
            # ticker has never had a real market snapshot at all, and
            # price-only refresh is only ever eligible for a ticker
            # that already has one. First-ever enrichment is
            # `ensure_company_enriched`'s own job, unrelated to this
            # lazy trigger.
            return PriceRefreshOutcome(attempted=False, succeeded=False, reason="no_prior_snapshot")
        known_currency = latest_snapshot.metadata.get("currency")
        if not known_currency:
            return PriceRefreshOutcome(attempted=False, succeeded=False, reason="no_confirmed_currency")
        known_shares_outstanding = latest_snapshot.metadata.get("shares_outstanding")

        resolved_evaluated_at = evaluated_at or datetime.now(timezone.utc)
        try:
            document = provider.fetch_price_only(
                company_identifier=ticker,
                evaluated_at=resolved_evaluated_at,
                known_currency=known_currency,
                known_shares_outstanding=known_shares_outstanding,
            )
        except BusinessDataProviderError as error:
            return PriceRefreshOutcome(attempted=True, succeeded=False, reason=str(error))

        result = ingest(
            document,
            existing_records=existing,
            evaluated_at=resolved_evaluated_at,
            canonical_security_id=latest_snapshot.canonical_security_id,
            resolution_version=latest_snapshot.resolution_version,
            identity_resolved_at=latest_snapshot.identity_resolved_at,
            provider_evidence_reference=latest_snapshot.provider_evidence_reference,
        )
        if isinstance(result, IngestedRecord):
            repository.add(result.record)
            succeeded = True
            return PriceRefreshOutcome(attempted=True, succeeded=True, reason="ok")
        # DuplicateRecord (identical price/trading day already stored)
        # is still a real, successful confirmation that today's price
        # is unchanged -- not a failure.
        succeeded = True
        return PriceRefreshOutcome(attempted=True, succeeded=True, reason=type(result).__name__.lower())
    finally:
        coordinator.finish(ticker, succeeded=succeeded)
