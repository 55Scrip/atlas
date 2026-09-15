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

**Listed siblings refresh together.** An issuer whose common equity is
listed as several securities (a Class A and a Class C listing, say) is
valued on one date on which every listed class has its own price
(`atlas.alpha.issuer_equity`). Refreshing one of them alone leaves its
siblings on other trading days, and the valuation is withheld until they
meet again. `refresh_prices_with_listed_siblings` therefore refreshes the
requested security and every listed sibling the caller names in one
pass: one call each, in order, on the caller's single provider instance
(so its pacing holds), after claiming all of them and reserving one call
each at once -- or none, making no call. The first failure ends the pass;
whatever did land stays, and the valuation keeps withholding until the
siblings share a date. A security with no listed siblings takes exactly
the single refresh it always did.
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

__all__ = [
    "PriceRefreshCoordinator",
    "PriceFreshnessStatus",
    "CoordinatedPriceRefreshOutcome",
    "refresh_price_only",
    "refresh_prices_with_listed_siblings",
    "price_freshness_status",
]

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

    def try_reserve(self, tickers: tuple[str, ...], *, remaining: int) -> str | None:
        """Claims every ticker at once, or none: `None` when claimed;
        `"already_refreshing"` when any is in flight; `"quota_insufficient"`
        when today's remaining budget, less one call for every refresh
        already in flight, cannot cover one call per ticker. The claim and
        the budget check share this lock, so two coordinated refreshes can
        never both count on the same last calls."""
        with self._lock:
            if any(t in self._in_flight for t in tickers):
                return "already_refreshing"
            if remaining - len(self._in_flight) < len(tickers):
                return "quota_insufficient"
            self._in_flight.update(tickers)
            for t in tickers:
                self._last_failed.discard(t)
            return None

    def release(self, ticker: str) -> None:
        """Ends a claim whose refresh was never attempted -- no failure
        is recorded for a call that was never made."""
        with self._lock:
            self._in_flight.discard(ticker)

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
        outcome = _refresh_claimed(ticker, provider=provider, repository=repository, quota=quota,
                                   evaluated_at=evaluated_at)
        succeeded = outcome.succeeded
        return outcome
    finally:
        coordinator.finish(ticker, succeeded=succeeded)


def _refresh_claimed(
    ticker: str,
    *,
    provider: AlphaVantageMarketDataProvider,
    repository: SqlAlchemyBusinessRecordRepository,
    quota: AlphaVantageQuotaTracker,
    evaluated_at: datetime | None,
) -> PriceRefreshOutcome:
    """One refresh of a ticker its caller has already claimed."""
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
        return PriceRefreshOutcome(attempted=True, succeeded=True, reason="ok")
    # DuplicateRecord (identical price/trading day already stored)
    # is still a real, successful confirmation that today's price
    # is unchanged -- not a failure.
    return PriceRefreshOutcome(attempted=True, succeeded=True, reason=type(result).__name__.lower())


@dataclass(frozen=True)
class CoordinatedPriceRefreshOutcome:
    """One refresh pass over a security and its listed siblings. The
    requested security's own outcome answers `attempted`/`succeeded`, so a
    caller of the single refresh reads it unchanged; `synchronized` is
    `None` without siblings, otherwise whether every security's latest
    stored quote now shares one trading day."""

    requested: str
    outcomes: tuple[tuple[str, PriceRefreshOutcome], ...]
    trading_days: tuple[tuple[str, date | None], ...]
    synchronized: bool | None
    reason: str

    @property
    def attempted(self) -> bool:
        return self.outcomes[0][1].attempted if self.outcomes else False

    @property
    def succeeded(self) -> bool:
        return self.outcomes[0][1].succeeded if self.outcomes else False


def _latest_quote_day(repository: SqlAlchemyBusinessRecordRepository, ticker: str) -> date | None:
    latest = _latest_market_snapshot_record(repository.get_by_company(ticker))
    return latest.period_end if latest is not None else None


def refresh_prices_with_listed_siblings(
    ticker: str,
    *,
    siblings: tuple[str, ...],
    provider: AlphaVantageMarketDataProvider,
    repository: SqlAlchemyBusinessRecordRepository,
    quota: AlphaVantageQuotaTracker,
    coordinator: PriceRefreshCoordinator,
    evaluated_at: datetime | None = None,
) -> CoordinatedPriceRefreshOutcome:
    """Refreshes `ticker` and every listed sibling in `siblings` (the other
    listed classes its issuer's valuation needs, as the caller resolved
    them) -- see this module's docstring. Never raises on a provider
    failure; siblings are refreshed here directly, never through this
    function again, so a pass never recurses."""
    others = tuple(sorted({s for s in siblings if s and s != ticker}))
    if not others:
        outcome = refresh_price_only(ticker, provider=provider, repository=repository, quota=quota,
                                     coordinator=coordinator, evaluated_at=evaluated_at)
        return CoordinatedPriceRefreshOutcome(ticker, ((ticker, outcome),), (), None, outcome.reason)

    securities = (ticker, *others)
    refused = coordinator.try_reserve(securities, remaining=quota.remaining_today())
    if refused is not None:
        not_attempted = PriceRefreshOutcome(attempted=False, succeeded=False, reason=refused)
        return CoordinatedPriceRefreshOutcome(
            ticker, tuple((s, not_attempted) for s in securities),
            tuple((s, _latest_quote_day(repository, s)) for s in securities), False, refused)

    outcomes: list[tuple[str, PriceRefreshOutcome]] = []
    failed: str | None = None
    pending = list(securities)
    try:
        while pending:
            security = pending.pop(0)
            if failed is not None:
                coordinator.release(security)
                outcomes.append((security, PriceRefreshOutcome(attempted=False, succeeded=False,
                                                               reason=f"not_attempted_after_{failed}_failed")))
                continue
            succeeded = False
            try:
                outcome = _refresh_claimed(security, provider=provider, repository=repository, quota=quota,
                                           evaluated_at=evaluated_at)
                succeeded = outcome.succeeded
            finally:
                coordinator.finish(security, succeeded=succeeded)
            outcomes.append((security, outcome))
            if not outcome.succeeded:
                failed = security
    finally:
        for security in pending:
            coordinator.release(security)

    days = tuple((s, _latest_quote_day(repository, s)) for s in securities)
    synchronized = None not in {d for _, d in days} and len({d for _, d in days}) == 1
    if failed is not None:
        reason = f"listed_sibling_refresh_failed:{failed}"
    elif not synchronized:
        reason = "listed_siblings_not_synchronized"
    else:
        reason = outcomes[0][1].reason
    return CoordinatedPriceRefreshOutcome(ticker, tuple(outcomes), days, synchronized, reason)
