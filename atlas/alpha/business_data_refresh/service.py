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

**Company Data Foundation v1: the gate is `assess_data_completeness
.is_minimally_complete`, not "any record at all."** The original gate
("does this company already have at least one persisted
`BusinessRecord`, of any kind") was too coarse: a company whose only
persisted record was, say, a single `MARKET_DATA_SNAPSHOT` (SEC failed
or is unsupported for this ticker; Alpha Vantage's own profile fetch
also failed transiently) permanently blocked every future enrichment
attempt, even though Atlas never actually recovered any identity or
fundamentals for it. The new gate requires real `COMPANY_PROFILE` or
`FINANCIAL_STATEMENT` coverage -- see `completeness.py`'s own docstring
for the exact predicate.

**This still bounds retries; it does not create a background poller.**
A ticker either provider can genuinely serve becomes minimally complete
on its first successful refresh and never re-fetches again after that
-- identical behavior to before for the common case. Only a ticker
*neither* provider can ever serve (e.g. a foreign filer SEC does not
cover, on a deployment with no Alpha Vantage key configured) keeps
attempting a fresh `refresh_company_data` on every subsequent
Watchlist/Portfolio add -- a real, bounded cost paid only for a company
Atlas genuinely has nothing for yet, triggered only by an explicit user
action, never a schedule.

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

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.completeness import assess_data_completeness
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
from atlas.alpha.business_data_refresh.models import ProviderFailure, RefreshSummary
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
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

    profile_documents: list[RawBusinessDocument] = []
    for provider in providers:
        if not isinstance(provider, CompanyProfileProvider):
            continue
        provider_id = f"{type(provider).__name__}.fetch_company_profile"
        provider_ids.append(provider_id)
        try:
            fetched = provider.fetch_company_profile(company_identifier=ticker, evaluated_at=evaluated_at)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc)))
            continue
        profile_documents.extend(fetched)

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
        )

    identity = decision.provenance
    _ingest_documents(tuple(profile_documents))

    for provider in providers:
        provider_id = type(provider).__name__
        provider_ids.append(provider_id)
        try:
            documents = provider.fetch(company_identifier=ticker, evaluated_at=evaluated_at)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc)))
            continue
        _ingest_documents(documents)

    for provider in providers:
        if not isinstance(provider, HistoricalMarketDataProvider):
            continue
        provider_id = f"{type(provider).__name__}.fetch_historical_snapshots"
        filing_dates = _known_filing_dates(known_records)
        if not filing_dates:
            continue
        try:
            historical_documents = provider.fetch_historical_snapshots(
                company_identifier=ticker, filing_dates=filing_dates, evaluated_at=evaluated_at
            )
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc)))
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
    for provider in providers:
        if not isinstance(provider, EarningsCallTranscriptProvider):
            continue
        provider_id = f"{type(provider).__name__}.fetch_earnings_call_transcripts"
        try:
            transcript_documents = provider.fetch_earnings_call_transcripts(
                company_identifier=ticker, evaluated_at=evaluated_at
            )
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed (Phase 13)
            provider_errors.append(ProviderFailure(provider_id=provider_id, error=str(exc)))
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
    )


def ensure_company_enriched(
    ticker: str,
    providers: tuple[BusinessDataProvider, ...],
    repository: SqlAlchemyBusinessRecordRepository,
    *,
    identity_gate: CanonicalSecurityIdentityGate,
) -> RefreshSummary | None:
    """Idempotent, automatic-trigger wrapper for the Investment Case
    Engine v1 slice's "add a company" write paths (Watchlist/Portfolio).

    Returns `None` -- no provider called at all -- if `ticker` already
    has enough persisted `BusinessRecord`s to be `assess_data_completeness
    .is_minimally_complete` (Company Data Foundation v1; see this
    module's own docstring for exactly why "any record at all" was too
    coarse a gate). A ticker that is not yet minimally complete --
    including one with no records at all, and one with only a stray
    record that never established real identity or fundamentals --
    delegates to `refresh_company_data`, whose own per-provider
    isolation already guarantees this never raises for a provider
    failure -- a caller on the Case-creation path may call this
    unconditionally without risking Case creation itself failing
    because of a transient provider outage.
    """
    existing = repository.get_by_company(ticker)
    if existing and assess_data_completeness(existing).is_minimally_complete:
        return None
    return refresh_company_data(ticker, providers, repository, identity_gate=identity_gate)
