"""`refresh_company_data` (ATLAS-031, Phase 17) -- the one canonical
application/use-case operation that ever calls a real
`BusinessDataProvider`.

Fetches from every given provider **independently**: one provider's
failure is recorded in `RefreshSummary.provider_errors` and never
blocks another provider's documents from being ingested (Phase 17's
own "report what changed," not "abort on first error"). Runs every
successfully fetched document through the existing, unmodified
`business_data.pipeline.ingest`, using this company's already-
persisted records as `existing_records` so versioning/duplicate-
detection are correct across process runs -- the exact gap Phase 16's
persistence layer exists to close.

**Never evaluates anything.** No Growth, Capital Allocation,
Valuation, Risk, Conviction, or Recommendation call anywhere in this
module -- those remain downstream consumers of the `BusinessRecord`s
this writes, read fresh the next time
`InvestmentCaseCompositionService` composes this company's Case.

**ATLAS-032, Phase 7: an optional second pass for historical market
data.** After the normal per-provider loop, any provider that also
implements `business_data.providers.HistoricalMarketDataProvider`
(checked via `isinstance` against that `runtime_checkable` Protocol --
never a hardcoded import of a specific provider class, preserving the
same provider-agnostic property `BusinessDataProvider` itself already
has, proven by the swappability tests) is asked for historical
snapshots covering every distinct fundamental-filing date already
known for this company -- freshly fetched this run or already
persisted. This is the one place `refresh_company_data` reads
`known_records` for something other than duplicate detection; the
provider itself never touches the repository or knows what a
`BusinessRecord` is.

**Investment Case Engine v1 slice: a third, identically-shaped optional
pass for `business_data.providers.CompanyProfileProvider`.** Any
provider that also implements it is asked, once, for this company's
descriptive identity fields -- the same `isinstance`-checked,
provider-agnostic pattern as the historical-market-data pass above,
never a hardcoded provider name.

**Capability Expansion Sprint 2: a fourth, identically-shaped optional
pass for `business_data.providers.EarningsCallTranscriptProvider`.**
Any provider that also implements it is asked, once, for its own
most-recently-ended quarter's earnings call transcript -- the same
`isinstance`-checked pattern once more, never a hardcoded provider
name. Unlike the historical-market-data pass, this one needs no
`known_records`-derived input: the provider itself owns the one real
piece of domain knowledge (its own transcript cadence) needed to turn
`evaluated_at` into a request.

**`ensure_company_enriched` is this slice's own automatic-trigger
entrypoint**, layered on top of `refresh_company_data` rather than
replacing it: the CLI and any future explicit "force refresh" caller
still want `refresh_company_data`'s unconditional behavior, but the
Watchlist/Portfolio "add a company" write paths must never re-fetch (or
re-call rate-limited providers for) a ticker Atlas has already
meaningfully enriched.

**Company Data Foundation v1 (superseded by Automatic Enrichment
Coverage, Implementation Phase 1): the gate is now per-provider, not a
single whole-ticker boolean.** The original gate ("does this company
already have at least one persisted `BusinessRecord`, of any kind") was
too coarse; Company Data Foundation v1 narrowed it to `assess_data
_completeness.is_minimally_complete` (`has_profile or has_statements`)
-- an improvement, but still a single boolean that could not
distinguish "SEC succeeded, Alpha Vantage never got a chance to run"
from "both succeeded," so a ticker with only one provider's data stayed
permanently unenriched for the other. `completion.assess_enrichment
_completion` (see that module's own docstring) is the real fix:
Alpha Vantage identity and SEC fundamentals are tracked independently,
each `SUCCEEDED`/`NOT_YET_ATTEMPTED`/`FAILED_TRANSIENT`/
`FAILED_UNSUPPORTED`.

**This still bounds retries; it does not create a background poller.**
A required provider that already `SUCCEEDED`, or that failed in a way
classified `FAILED_UNSUPPORTED` (a genuine, permanent per-ticker/filer
mismatch -- never re-attempted, Requirement 8's own "not retried as
though it were a transient failure"), is never re-fetched. A required
provider that is `NOT_YET_ATTEMPTED` or `FAILED_TRANSIENT` (e.g. a
still-unconfigured Alpha Vantage API key) keeps attempting a fresh
`refresh_company_data` on every subsequent explicit Watchlist/Portfolio
action -- a real, bounded cost paid only for a company Atlas genuinely
still has real, retryable work left for, triggered only by an explicit
user action, never a schedule (periodic automatic recovery is
explicitly out of this sprint's scope).

**Sprint O: the Canonical Security Identity Gate is now mandatory.**
`identity_gate` is a required keyword-only argument -- there is no
optional/bypass path at this layer, matching the brief's own "no
fallback, no provider retry" instruction. Every `CompanyProfileProvider`
this ticker's `providers` include is asked for its identity data
*first*, before any fundamentals/market-data document is fetched;
`identity_gate.evaluate()` runs exactly once against whatever identity
candidates that produces, and only an `AUTO_ACCEPT` decision lets this
function proceed to fetch and ingest anything else at all. Every other
outcome (`MANUAL_CONFIRMATION`/`LOW_CONFIDENCE`/`AMBIGUOUS`/`NO_MATCH`/
`REJECT`) short-circuits the whole run -- SEC EDGAR's fundamentals call
is never even made -- and is reported via
`RefreshSummary.identity_gate_outcome`/`identity_gate_reason`, never
raised or silently swallowed. Every `BusinessRecord` this function
ingests within one allowed run (the profile document included) carries
the identical `CanonicalSecurity` provenance the gate returned.
"""
from __future__ import annotations

from dataclasses import replace

from datetime import date, datetime, timezone
from typing import Callable

from atlas.analysis_engine.business_data.models import BusinessRecord, RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import IngestionRejected, ingest
from atlas.analysis_engine.business_data.providers import (
    BusinessDataProvider,
    CompanyProfileProvider,
    EarningsCallTranscriptProvider,
    HistoricalMarketDataProvider,
)
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import DuplicateRecord
from atlas.alpha.business_data_refresh.completion import assess_enrichment_completion
from atlas.alpha.business_data_refresh.models import (
    EnrichmentDepth,
    ProviderFailure,
    RefreshSummary,
    stage_allowed,
)
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.business_data_providers.errors import DailyQuotaExhausted, RateLimited
from atlas.alpha.canonical_security_gate.provenance import BusinessRecordIdentityProvenance

__all__ = ["refresh_company_data", "ensure_company_enriched"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _known_filing_dates(records: list[BusinessRecord]) -> tuple[date, ...]:
    """Every distinct date a fundamental became public -- the caller
    Phase 7's sampling rule needs, sourced from real, already-ingested
    `BusinessRecord.published_at` values, never invented."""
    return tuple(sorted({record.published_at.date() for record in records if record.document_type is SourceKind.FINANCIAL_STATEMENT}))


def refresh_company_data(
    ticker: str,
    providers: tuple[BusinessDataProvider, ...],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
    depth: EnrichmentDepth = EnrichmentDepth.FULL,
    budget_available: "Callable[[], bool] | None" = None,
    on_provider_throttled: "Callable[[Exception], None] | None" = None,
    provider_symbol: "Callable[[str, str | None], str] | None" = None,
) -> RefreshSummary:
    """One `evaluated_at` timestamp for the whole run (every document
    from every provider is fetched "as of now" together, not at
    slightly different instants). `existing_records` starts from the
    repository's own current state for this company and is extended
    in-memory as new records are produced within this same run -- one
    initial read, not one read per document -- so a later document in
    the same fetch correctly sees an earlier document's new record
    without a redundant round trip (each period is its own lineage, so
    this matters for read efficiency, not correctness, but it is the
    cheap thing to do regardless).

    Sprint O: `CompanyProfileProvider.fetch_company_profile()` now runs
    *first*, for every provider that implements it, before any other
    fetch -- its documents are the only source of identity candidates
    `identity_gate.evaluate()` can see. If the gate does not return
    `allowed=True`, this function returns immediately: no fundamentals
    call, no historical-snapshot call, no `BusinessRecord` of any kind
    is created for this run. See this module's own docstring for why.
    """
    evaluated_at = _utc_now()
    known_records: list[BusinessRecord] = list(repository.get_by_company(ticker))
    completed_stages: list[str] = []
    stopped_for_budget = False
    identity_blocked_by_throttling = False
    daily_quota_exhausted = False

    def _may_run(stage: str) -> bool:
        """Calibration Phase 8B. Two independent gates, checked in this
        order and never collapsed: the requested `depth` decides whether
        a stage is *wanted*, and `budget_available` decides whether
        there is provider budget left to run it *now*.

        Budget is re-checked before every remaining stage rather than
        once per company (Phase 8B's own finding: `bulk.py` checked the
        budget only *between* tickers, so one company could overshoot
        by every call after its first). Stopping here is always
        graceful: every stage already completed stays fully ingested
        and persisted, and a stage never started remains genuinely
        `NOT_YET_ATTEMPTED` for `assess_enrichment_completion`, so the
        next run resumes it as ordinary retryable work rather than
        treating it as a failure."""
        nonlocal stopped_for_budget
        if not stage_allowed(depth, stage):
            return False
        if budget_available is not None and not budget_available():
            stopped_for_budget = True
            return False
        return True

    provider_ids: list[str] = []
    fetched_documents = 0
    new_records = 0
    new_versions = 0
    duplicates_skipped = 0
    rejected_documents = 0
    provider_errors: list[ProviderFailure] = []
    changed_records: list[BusinessRecord] = []
    identity: BusinessRecordIdentityProvenance | None = None

    def _ingest_documents(documents: tuple) -> None:
        nonlocal fetched_documents, new_records, new_versions, duplicates_skipped, rejected_documents
        for document in documents:
            fetched_documents += 1
            result = ingest(
                document,
                existing_records=tuple(known_records),
                evaluated_at=evaluated_at,
                canonical_security_id=identity.canonical_security_id if identity is not None else None,
                resolution_version=identity.resolution_version if identity is not None else None,
                identity_resolved_at=identity.resolved_at if identity is not None else None,
                provider_evidence_reference=identity.provider_evidence_reference if identity is not None else None,
            )
            if isinstance(result, IngestionRejected):
                rejected_documents += 1
                continue
            if isinstance(result, DuplicateRecord):
                duplicates_skipped += 1
                continue
            record = result.record
            repository.add(record)
            known_records.append(record)
            changed_records.append(record)
            if record.version.version_number == 1:
                new_records += 1
            else:
                new_versions += 1

    if not _may_run("profile"):
        # No budget for even the one call that decides whether this
        # company can be analysed at all. Return *without* calling the
        # gate: `identity_gate.evaluate()` persists every attempt it is
        # given, and recording a `NO_MATCH` here would permanently
        # claim "no provider returned any identity candidate for this
        # ticker" when the truth is "Atlas never asked." That is
        # exactly the one-word-meaning-several-things failure this
        # sprint exists to remove.
        return RefreshSummary(
            ticker=ticker,
            providers_attempted=(),
            fetched_documents=0,
            new_records=0,
            new_versions=0,
            duplicates_skipped=0,
            rejected_documents=0,
            provider_errors=(),
            identity_gate_outcome="NOT_ATTEMPTED",
            identity_gate_reason="Provider budget exhausted before identity resolution was attempted.",
            changed_records=(),
            evaluated_at=evaluated_at,
            depth=depth,
            completed_stages=(),
            stopped_for_budget=stopped_for_budget,
            daily_quota_exhausted=daily_quota_exhausted,
        )

    def _symbol_for(provider: object) -> str:
        """Which string this provider is asked about.

        Berkshire Class B is the case this exists for: Atlas, the
        portfolio and the user know it as `BRK.B`, and Alpha Vantage
        answers only to `BRK-B` (verified live, one request). The
        resolver is injected rather than imported -- this package may
        not import `canonical_security` -- and it performs a lookup of
        a stored, human-approved route. It never derives one spelling
        from another: a ticker with no route, or a provider that
        declares no name, goes out unchanged.
        """
        if provider_symbol is None:
            return ticker
        return provider_symbol(ticker, getattr(provider, "canonical_provider_name", None))

    def _as_canonical(documents: tuple, symbol: str) -> tuple:
        """Route the request out, bring the answer back under Atlas's
        own name.

        Providers stamp `company` on their documents from whatever
        symbol they were handed, so without this a routed fetch would
        persist records under `BRK-B` -- the provider's spelling
        leaking into the field every join, the portfolio and the
        security-provenance work all key on. Rewriting is confined to
        genuinely routed fetches, so the unrouted path is byte-for-byte
        unchanged.

        Only `company` is rewritten. `identifier` keeps the provider's
        own spelling, which is honest: it names the provider's evidence,
        not Atlas's security.
        """
        if symbol == ticker:
            return documents
        return tuple(
            replace(document, company=ticker) if document.company != ticker else document
            for document in documents
        )

    profile_documents: list[RawBusinessDocument] = []
    for provider in providers:
        if not isinstance(provider, CompanyProfileProvider):
            continue
        provider_id = f"{type(provider).__name__}.fetch_company_profile"
        provider_ids.append(provider_id)
        try:
            symbol = _symbol_for(provider)
            fetched = _as_canonical(
                provider.fetch_company_profile(company_identifier=symbol, evaluated_at=evaluated_at),
                symbol,
            )
        except RateLimited as exc:
            # Provider & Quota Intelligence. A throttled call produced no
            # identity evidence *about this company* -- it never got that
            # far. Recorded like any other failure, but also flagged so
            # the identity gate below is skipped entirely (see the
            # `identity_blocked_by_throttling` branch) rather than being
            # handed zero candidates and persisting a `NO_MATCH` that
            # would permanently assert a company fact Atlas never
            # established.
            identity_blocked_by_throttling = True
            if isinstance(exc, DailyQuotaExhausted):
                daily_quota_exhausted = True
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc), kind=type(exc).__name__))
            if on_provider_throttled is not None:
                on_provider_throttled(exc)
            continue
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            if isinstance(exc, DailyQuotaExhausted):
                # Provider & Quota Intelligence: the provider's own word
                # that the day is spent. Flagged so a batch caller aborts
                # rather than attempting the next company.
                daily_quota_exhausted = True
                if on_provider_throttled is not None:
                    on_provider_throttled(exc)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc), kind=type(exc).__name__))
            continue
        profile_documents.extend(fetched)

    if identity_blocked_by_throttling and not profile_documents:
        # Provider & Quota Intelligence, Requirement 4. `identity_gate
        # .evaluate()` persists *every* attempt it is given, including
        # the zero-candidate case, as a `NO_MATCH` resolution record
        # meaning "no provider returned any identity-bearing candidate
        # for this ticker." That sentence is false when the provider
        # refused to answer at all: nothing was learned about the
        # company. Returning before the gate keeps a throttled attempt
        # from leaving evidence behind, and reports the real cause
        # instead.
        return RefreshSummary(
            ticker=ticker,
            providers_attempted=tuple(provider_ids),
            fetched_documents=0,
            new_records=0,
            new_versions=0,
            duplicates_skipped=0,
            rejected_documents=0,
            provider_errors=tuple(provider_errors),
            identity_gate_outcome="NOT_EVALUATED_PROVIDER_THROTTLED",
            identity_gate_reason=(
                "The provider was rate limited before returning any identity data, so identity was "
                "never evaluated for this company. This is not a statement about the company."
            ),
            changed_records=(),
            evaluated_at=evaluated_at,
            depth=depth,
            completed_stages=(),
            stopped_for_budget=stopped_for_budget,
            daily_quota_exhausted=daily_quota_exhausted,
        )

    decision = identity_gate.evaluate(
        ticker=ticker, documents=tuple(profile_documents), clock=lambda: evaluated_at
    )
    if not decision.allowed:
        return RefreshSummary(
            ticker=ticker,
            providers_attempted=tuple(provider_ids),
            fetched_documents=0,
            new_records=0,
            new_versions=0,
            duplicates_skipped=0,
            rejected_documents=0,
            provider_errors=tuple(provider_errors),
            identity_gate_outcome=decision.outcome,
            identity_gate_reason=decision.reason,
            changed_records=(),
            evaluated_at=evaluated_at,
            depth=depth,
            completed_stages=(),
            stopped_for_budget=stopped_for_budget,
            daily_quota_exhausted=daily_quota_exhausted,
        )

    identity = decision.provenance
    _ingest_documents(tuple(profile_documents))
    completed_stages.append("profile")

    for provider in providers:
        if not _may_run("fundamentals"):
            break
        provider_id = type(provider).__name__
        provider_ids.append(provider_id)
        try:
            symbol = _symbol_for(provider)
            documents = _as_canonical(
                provider.fetch(company_identifier=symbol, evaluated_at=evaluated_at), symbol
            )
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            if isinstance(exc, DailyQuotaExhausted):
                # Provider & Quota Intelligence: the provider's own word
                # that the day is spent. Flagged so a batch caller aborts
                # rather than attempting the next company.
                daily_quota_exhausted = True
                if on_provider_throttled is not None:
                    on_provider_throttled(exc)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc), kind=type(exc).__name__))
            continue
        _ingest_documents(documents)

    if stage_allowed(depth, "fundamentals") and not stopped_for_budget:
        completed_stages.append("fundamentals")

    for provider in providers:
        if not isinstance(provider, HistoricalMarketDataProvider):
            continue
        if not _may_run("historical"):
            break
        provider_id = f"{type(provider).__name__}.fetch_historical_snapshots"
        filing_dates = _known_filing_dates(known_records)
        if not filing_dates:
            continue
        try:
            historical_documents = provider.fetch_historical_snapshots(
                company_identifier=(symbol := _symbol_for(provider)),
                filing_dates=filing_dates,
                evaluated_at=evaluated_at,
            )
            historical_documents = _as_canonical(historical_documents, symbol)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            if isinstance(exc, DailyQuotaExhausted):
                # Provider & Quota Intelligence: the provider's own word
                # that the day is spent. Flagged so a batch caller aborts
                # rather than attempting the next company.
                daily_quota_exhausted = True
                if on_provider_throttled is not None:
                    on_provider_throttled(exc)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc), kind=type(exc).__name__))
            continue
        _ingest_documents(historical_documents)

    # Capability Expansion Sprint 2: a fourth, identically-shaped
    # optional pass -- any provider that also implements
    # `EarningsCallTranscriptProvider` is asked, once, for its own
    # most-recently-ended quarter's transcript. Unlike the historical-
    # market-data pass above, this needs no `known_records`-derived
    # date list: the provider itself derives which quarter to request
    # from `evaluated_at` alone (see that Protocol's own docstring for
    # why).
    if stage_allowed(depth, "historical") and not stopped_for_budget:
        completed_stages.append("historical")

    for provider in providers:
        if not isinstance(provider, EarningsCallTranscriptProvider):
            continue
        if not _may_run("transcripts"):
            break
        provider_id = f"{type(provider).__name__}.fetch_earnings_call_transcripts"
        try:
            transcript_documents = provider.fetch_earnings_call_transcripts(
                company_identifier=(symbol := _symbol_for(provider)), evaluated_at=evaluated_at
            )
            transcript_documents = _as_canonical(transcript_documents, symbol)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            if isinstance(exc, DailyQuotaExhausted):
                # Provider & Quota Intelligence: the provider's own word
                # that the day is spent. Flagged so a batch caller aborts
                # rather than attempting the next company.
                daily_quota_exhausted = True
                if on_provider_throttled is not None:
                    on_provider_throttled(exc)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc), kind=type(exc).__name__))
            continue
        _ingest_documents(transcript_documents)

    return RefreshSummary(
        ticker=ticker,
        providers_attempted=tuple(provider_ids),
        fetched_documents=fetched_documents,
        new_records=new_records,
        new_versions=new_versions,
        duplicates_skipped=duplicates_skipped,
        rejected_documents=rejected_documents,
        provider_errors=tuple(provider_errors),
        identity_gate_outcome=decision.outcome,
        identity_gate_reason=None,
        changed_records=tuple(changed_records),
        evaluated_at=evaluated_at,
        depth=depth,
        completed_stages=tuple(completed_stages)
        + (("transcripts",) if stage_allowed(depth, "transcripts") and not stopped_for_budget else ()),
        stopped_for_budget=stopped_for_budget,
        daily_quota_exhausted=daily_quota_exhausted,
    )


def ensure_company_enriched(
    ticker: str,
    providers: tuple[BusinessDataProvider, ...],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
    known_provider_failures: tuple[ProviderFailure, ...] = (),
    depth: EnrichmentDepth = EnrichmentDepth.FULL,
    budget_available: "Callable[[], bool] | None" = None,
) -> RefreshSummary | None:
    """Idempotent, automatic-trigger wrapper for the Investment Case
    Engine v1 slice's "add a company" write paths (Watchlist/Portfolio).

    Returns `None` -- no provider called at all -- only when
    `completion.assess_enrichment_completion` finds no retryable work
    left for this ticker: every required provider (Alpha Vantage
    identity, SEC fundamentals) has either already succeeded, or failed
    in a way classified `UNSUPPORTED` (Automatic Enrichment Coverage,
    Implementation Phase 1 -- replaces this function's own prior,
    coarser `assess_data_completeness.is_minimally_complete` gate, which
    treated any *one* successful provider as permanent, whole-ticker
    "done" and could never distinguish "this provider never got a
    chance to run" from "this provider will never succeed here"; see
    `completion.py`'s own module docstring for the full rationale).

    `known_provider_failures` is the caller's own most recently
    persisted `IngestionResult.provider_failures` for this ticker (empty
    by default) -- this function performs no repository lookup for it
    itself, keeping this module free of any dependency on
    `atlas.alpha.ingestion` (see `completion.py`'s own docstring for
    why that dependency direction would be circular).

    A ticker with retryable work delegates to `refresh_company_data`,
    whose own per-provider isolation already guarantees this never
    raises for a provider failure -- a caller on the Case-creation path
    may call this unconditionally without risking Case creation itself
    failing because of a transient provider outage.
    """
    existing = repository.get_by_company(ticker)
    completion = assess_enrichment_completion(ticker, existing, known_provider_failures)
    if not completion.has_retryable_work:
        return None
    return refresh_company_data(
        ticker,
        providers,
        repository,
        identity_gate=identity_gate,
        depth=depth,
        budget_available=budget_available,
    )
