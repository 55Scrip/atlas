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
it has no knowledge of `AlphaHolding`/`Case` at all. "No duplicate
Cases" therefore holds trivially -- Case creation/reuse is exactly
whatever `CaseGenerationService`/`_ensure_cases` already guaranteed
before this module existed, untouched.
"""
from __future__ import annotations

from atlas.alpha.business_data_refresh.models import BulkEnrichmentSummary, EnrichmentOutcome, HoldingEnrichmentResult
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.analysis_engine.business_data.providers import BusinessDataProvider

__all__ = ["enrich_holdings"]


def enrich_holdings(
    tickers: tuple[str, ...],
    providers: tuple[BusinessDataProvider, ...],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
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
    """
    results: list[HoldingEnrichmentResult] = []
    for ticker in tickers:
        try:
            summary = ensure_company_enriched(ticker, providers, repository, identity_gate=identity_gate)
        except Exception as exc:  # noqa: BLE001 -- one ticker's unexpected failure must never abort the batch
            results.append(HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.FAILED, detail=str(exc)))
            continue

        if summary is None:
            results.append(
                HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.SKIPPED_ALREADY_ENRICHED, detail=None)
            )
        elif summary.new_records > 0 or summary.new_versions > 0:
            results.append(HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.ENRICHED, detail=None))
        else:
            detail = "; ".join(f"{failure.provider_id}: {failure.error}" for failure in summary.provider_errors) or None
            results.append(HoldingEnrichmentResult(ticker=ticker, outcome=EnrichmentOutcome.UNSUPPORTED, detail=detail))

    return BulkEnrichmentSummary(results=tuple(results))
