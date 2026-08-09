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
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.pipeline import IngestionRejected, ingest
from atlas.analysis_engine.business_data.providers import BusinessDataProvider, HistoricalMarketDataProvider
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import DuplicateRecord
from atlas.alpha.business_data_refresh.models import ProviderFailure, RefreshSummary
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository

__all__ = ["refresh_company_data"]


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

    def _ingest_documents(documents: tuple) -> None:
        nonlocal fetched_documents, new_records, new_versions, duplicates_skipped, rejected_documents
        for document in documents:
            fetched_documents += 1
            result = ingest(document, existing_records=tuple(known_records), evaluated_at=evaluated_at)
            if isinstance(result, IngestionRejected):
                rejected_documents += 1
                continue
            if isinstance(result, DuplicateRecord):
                duplicates_skipped += 1
                continue
            record = result.record
            repository.add(record)
            known_records.append(record)
            if record.version.version_number == 1:
                new_records += 1
            else:
                new_versions += 1

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

    return RefreshSummary(
        ticker=ticker,
        providers_attempted=tuple(provider_ids),
        fetched_documents=fetched_documents,
        new_records=new_records,
        new_versions=new_versions,
        duplicates_skipped=duplicates_skipped,
        rejected_documents=rejected_documents,
        provider_errors=tuple(provider_errors),
    )
