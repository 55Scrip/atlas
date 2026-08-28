"""Bulk, rate-aware enrichment across every holding in a portfolio
(Internal Alpha Fix Sprint 1, Part 1 -- confirmed root cause IA-001).

`enrich_holdings` is the one function that turns a list of tickers into
a sequential run of `ensure_company_enriched` -- the exact same
idempotent, already-provider-isolated entrypoint the single-holding
Watchlist/Portfolio "add" paths already use, completely unchanged. This
module adds no new provider-calling logic and no new rate-limiting
logic of its own:

- `ensure_company_enriched` already skips a ticker that is
  `assess_data_completeness.is_minimally_complete` -- "already enriched
  companies skipped" and "partially enriched companies resumed" are
  both free consequences of that existing gate, not new behavior here.
- `refresh_company_data` already isolates one provider's failure from
  another's, and `AlphaVantageMarketDataProvider` already paces its own
  calls internally via a real, injectable sleeper.
- Calling this function again later re-attempts only the tickers that
  never became minimally complete -- "failed companies retry safely" is
  the same existing gate, not new retry logic.

All this module adds is the batch loop itself, plus per-ticker failure
isolation strong enough that an unexpected exception from one ticker (a
genuine bug, never a provider-reported failure -- those already come
back inside `RefreshSummary.provider_errors` and are reported as
`UNSUPPORTED`, not raised) can never abort the remaining tickers.

**Sequential, not concurrent, by design.** Providers are shared,
rate-limited resources (Alpha Vantage's own free-tier quota; SEC
EDGAR's own fair-use expectation). Running many tickers concurrently
would defeat the pacing `AlphaVantageMarketDataProvider` already
enforces per provider *instance* -- this function is called with one
shared provider tuple for the whole batch, so sequential execution is
what makes that existing pacing meaningful across tickers, not just
within one ticker's own multiple calls. A future sprint may introduce a
bounded worker pool (each worker owning its own provider instances) if
sequential throughput becomes a real constraint; nothing here forecloses
that -- it is simply not needed to solve IA-001.

**Never touches Cases, never calls a Case-creation path.** This module
only ever writes `BusinessRecord`s through `ensure_company_enriched`;
it has no knowledge of `AlphaHolding`/`Case` beyond the one optional,
read-only `case_ids_by_ticker` mapping below (Automatic Enrichment
Coverage, Implementation Phase 1). "No duplicate Cases" still holds
trivially -- this module never creates, resolves, or reuses a Case,
only accepts one already resolved by its caller; Case creation/reuse
is exactly whatever `CaseGenerationService`/`_ensure_cases` already
guaranteed before this module existed, untouched.
"""
from __future__ import annotations

from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.models import BulkEnrichmentSummary, EnrichmentOutcome, HoldingEnrichmentResult
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.enrichment_tracking.store import EnrichmentProgressStore
from atlas.alpha.ingestion.engine import classify_refresh
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.analysis_engine.business_data.providers import BusinessDataProvider

__all__ = ["enrich_holdings"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def enrich_holdings(
    tickers: tuple[str, ...],
    providers: tuple[BusinessDataProvider, ...],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
    ingestion_result_repository: SqlAlchemyIngestionResultRepository | None = None,
    case_ids_by_ticker: dict[str, str] | None = None,
    quota_tracker: AlphaVantageQuotaTracker | None = None,
    progress_store: EnrichmentProgressStore | None = None,
    progress_batch_id: str | None = None,
) -> BulkEnrichmentSummary:
    """Deterministic given a deterministic set of provider responses:
    the only non-determinism comes from the underlying providers
    themselves (live network calls), the same as every other real
    provider-calling entrypoint in this codebase (`refresh_company_data`
    itself). A duplicate ticker in `tickers` is not de-duplicated here
    -- `ensure_company_enriched` is naturally idempotent (its own gate
    makes a second call for an already-complete ticker a no-op
    `SKIPPED_ALREADY_ENRICHED`), so a duplicate is harmless, just
    slightly wasteful; callers are expected to pass already-distinct
    tickers (every real call site does).

    `ingestion_result_repository` (Automatic Enrichment Coverage,
    Implementation Phase 1) is optional, the same progressively-
    enhancing `X | None = None` pattern this module's own dependencies
    already use. When supplied: (1) each ticker's prior `IngestionResult
    .provider_failures` (if any) is threaded into `ensure_company
    _enriched`, so a provider already known `FAILED_UNSUPPORTED` for
    that ticker is not retried (Requirement 8); (2) if `case_ids_by
    _ticker` also resolves this ticker to a real Case, this run's own
    result is persisted back as that Case's `IngestionResult` (reusing
    `classify_refresh`, exactly `AlphaPortfolioService`/
    `AlphaWatchlistService._trigger_enrichment`'s own existing pattern
    -- never a second, duplicate persistence mechanism), so the *next*
    bulk or single-ticker enrichment call can see it. Without both,
    `enrich_holdings` behaves exactly as it did before this field
    existed: every provider not yet `SUCCEEDED` stays retryable, and no
    Case is ever read or written.

    `quota_tracker`/`progress_store`/`progress_batch_id` (Zero-Effort
    Portfolio Onboarding) are optional, the same progressively-enhancing
    pattern every other dependency here already uses. When
    `quota_tracker` is given, a ticker's turn is skipped outright --
    `QUOTA_DEFERRED`, never attempted -- once the shared Alpha Vantage
    daily budget is exhausted, rather than letting it hit a live
    provider rate-limit error; this is the one real fix this sprint
    makes to the quota tracker being *tracked* but not *enforced* in
    this bulk path. When `progress_store`/`progress_batch_id` are given,
    each ticker's row in `enrichment_progress` is updated to `ANALYZING`
    before its call and `DONE`/`DEFERRED` after -- the one thing that
    makes this already-running background task's progress observable to
    a polling frontend, not a second scheduling mechanism.
    """
    results: list[HoldingEnrichmentResult] = []
    for ticker in tickers:
        if quota_tracker is not None and not quota_tracker.has_budget():
            results.append(
                HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.QUOTA_DEFERRED, detail=None)
            )
            if progress_store is not None and progress_batch_id is not None:
                progress_store.mark_deferred(progress_batch_id, ticker)
            continue

        if progress_store is not None and progress_batch_id is not None:
            progress_store.mark_analyzing(progress_batch_id, ticker)

        known_provider_failures: tuple = ()
        if ingestion_result_repository is not None:
            prior = ingestion_result_repository.get_by_ticker(ticker)
            if prior is not None:
                known_provider_failures = prior.provider_failures
        try:
            summary = ensure_company_enriched(
                ticker, providers, repository, identity_gate=identity_gate,
                known_provider_failures=known_provider_failures,
            )
        except Exception as exc:  # noqa: BLE001 -- one ticker's unexpected failure must never abort the batch
            results.append(HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.FAILED, detail=str(exc)))
            if progress_store is not None and progress_batch_id is not None:
                progress_store.mark_done(progress_batch_id, ticker)
            continue

        if progress_store is not None and progress_batch_id is not None:
            progress_store.mark_done(progress_batch_id, ticker)

        if summary is None:
            results.append(
                HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.SKIPPED_ALREADY_ENRICHED, detail=None)
            )
        elif summary.new_records > 0 or summary.new_versions > 0:
            results.append(HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.ENRICHED, detail=None))
        else:
            detail = "; ".join(f"{failure.provider_id}: {failure.error}" for failure in summary.provider_errors) or None
            results.append(HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.UNSUPPORTED, detail=detail))

        if summary is not None and ingestion_result_repository is not None and case_ids_by_ticker is not None:
            case_id = case_ids_by_ticker.get(ticker)
            if case_id is not None:
                result = classify_refresh(summary, ticker=ticker, case_id=case_id, ran_at=summary.evaluated_at or _utc_now())
                ingestion_result_repository.upsert(result)

    return BulkEnrichmentSummary(results=tuple(results))
