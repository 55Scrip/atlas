"""Business Data ingestion pipeline (ATLAS-022, Phase 6 orchestration).

Single public entry point: `ingest`. Runs the fixed stage order Phase 6
specifies -- Validation, then Normalization, then Versioning -- over
one `RawBusinessDocument` at a time, and returns one of three distinct,
named outcomes rather than raising for ordinary incompleteness (the
same "typed result, not an exception, for anything short of an actual
contract violation" rule every other pipeline in this codebase follows):

- `IngestedRecord` -- a new, valid `BusinessRecord` was assembled.
- `IngestionRejected` -- validation failed; carries every reason.
- `versioning.DuplicateRecord` -- the document's content exactly
  matches the current head of its lineage; nothing new was created.

**No AI, no semantic interpretation, no scoring anywhere in this
module or the stages it calls.** `ingest` never reads what a document
*says* -- only what a provider already told it structurally (an id, a
company, a kind, a timestamp, a hash).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.models import BusinessRecord, RawBusinessDocument, RecordVersion
from atlas.analysis_engine.business_data.normalization import normalize
from atlas.analysis_engine.business_data.validation import ValidationFailureReason, validate_raw_document
from atlas.analysis_engine.business_data.versioning import (
    DuplicateRecord,
    compute_lineage_id,
    determine_version,
)
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger

__all__ = [
    "IngestedRecord",
    "IngestionRejected",
    "IngestionResult",
    "ingest",
    "SHARE_COUNT_PROVENANCE_KEYS",
    "ProvenanceEnrichmentRefused",
    "enrich_provenance",
]

#: The SEC share-count provenance a financial statement may carry (see
#: `atlas.business_data_providers.sec_edgar._share_count_provenance`):
#: which filing the stored period-end count came from, and what the first
#: filing reported. Provenance, not content -- never in a statement's
#: content hash.
SHARE_COUNT_PROVENANCE_KEYS = frozenset({
    "shares_outstanding_filed",
    "shares_outstanding_accession",
    "shares_outstanding_first_reported",
    "shares_outstanding_first_reported_filed",
    "shares_outstanding_first_reported_accession",
})

#: Every BusinessRecord this pipeline produces is read the same way by
#: every surface identified as a future consumer -- mirrors
#: `atlas.analysis_engine.pipeline._ALL_INTENDED_CONSUMERS` exactly, so
#: a future sprint that narrows consumption per-record can do so
#: deliberately rather than by accident.
_ALL_INTENDED_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


@dataclass(frozen=True)
class IngestedRecord:
    record: BusinessRecord


@dataclass(frozen=True)
class IngestionRejected:
    reasons: tuple[ValidationFailureReason, ...]


IngestionResult = IngestedRecord | IngestionRejected | DuplicateRecord


def ingest(
    document: RawBusinessDocument,
    *,
    existing_records: tuple[BusinessRecord, ...] = (),
    evaluated_at: datetime,
    canonical_security_id: str | None = None,
    resolution_version: str | None = None,
    identity_resolved_at: datetime | None = None,
    provider_evidence_reference: str | None = None,
) -> IngestionResult:
    """Deterministic: identical `document`, `existing_records`, and
    `evaluated_at` always produce a deeply equal result. `evaluated_at`
    is the only timestamp anywhere in this call graph -- no stage reads
    a wall clock.

    `existing_records` is the caller's full known history (any number
    of unrelated lineages) -- `versioning.determine_version` filters
    internally to the one lineage this `document` belongs to. Passing
    `()` (the default) always yields version 1 of a brand-new lineage,
    since there is nothing to compare against.

    Sprint O Phase 8: the four `canonical_security_id`/
    `resolution_version`/`identity_resolved_at`/
    `provider_evidence_reference` keyword arguments are optional, plain
    primitives, passed straight through onto the resulting
    `BusinessRecord` unchanged -- this module still never imports
    `atlas.alpha.canonical_security_gate` or anything under
    `atlas.alpha`. The caller
    (`atlas.alpha.business_data_refresh.service.refresh_company_data`)
    is the one place that resolves an identity and supplies these; every
    other/older caller omits them and gets the same `None`-filled
    `BusinessRecord` this pipeline always produced.
    """
    failure_reasons = validate_raw_document(document)
    if failure_reasons:
        return IngestionRejected(reasons=failure_reasons)

    normalized = normalize(document)

    lineage_id = compute_lineage_id(
        provider_id=normalized.provider_id,
        source_kind=normalized.source_kind,
        company=normalized.company,
        identifier=normalized.identifier,
    )

    version_outcome = determine_version(
        lineage_id=lineage_id,
        content_hash=normalized.content_hash,
        existing_records=existing_records,
        created_at=evaluated_at,
    )
    if isinstance(version_outcome, DuplicateRecord):
        return version_outcome

    record = BusinessRecord(
        id=f"{lineage_id}:v{version_outcome.version_number}",
        lineage_id=lineage_id,
        identifier=normalized.identifier,
        company=normalized.company,
        document_type=normalized.source_kind,
        published_at=normalized.published_at,
        provider_id=normalized.provider_id,
        source_reference=normalized.raw_reference,
        content_hash=normalized.content_hash,
        version=version_outcome,
        provenance=Provenance(
            source_kind=SourceKind.EXTERNAL_DATA_SOURCE,
            source_references=(normalized.raw_reference,),
            dependencies=(),
            update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
            consumers=_ALL_INTENDED_CONSUMERS,
            computed_at=evaluated_at,
        ),
        validation_status=ValidationStatus.VALID,
        period_start=normalized.period_start,
        period_end=normalized.period_end,
        language=normalized.language,
        metadata=normalized.metadata,
        canonical_security_id=canonical_security_id,
        resolution_version=resolution_version,
        identity_resolved_at=identity_resolved_at,
        provider_evidence_reference=provider_evidence_reference,
    )
    return IngestedRecord(record=record)


class ProvenanceEnrichmentRefused(ValueError):
    """`enrich_provenance` was asked to change something that is not
    provenance -- a different document, different content, or a
    different value under a key it already holds."""


def enrich_provenance(
    document: RawBusinessDocument,
    *,
    head: BusinessRecord,
    provenance_keys: frozenset[str],
    evaluated_at: datetime,
) -> BusinessRecord | None:
    """The one deliberate exception to "a new version means new content"
    (Historical Market-Data Backfill): a stored record gains provenance its
    ingestion could not record yet, as a new version that supersedes it.

    Ingestion never does this on its own -- `determine_version` treats an
    unchanged content hash as a duplicate, which is right for a routine
    re-fetch and is exactly why provenance kept out of the hash never
    reaches a record already stored. This is only for an operator's
    explicit enrichment, and it is refused unless the document is the same
    lineage with the same content hash, every metadata key `head` holds is
    repeated exactly, and every provenance key `head` already holds carries
    the same value. The new version keeps `head`'s content hash (the content
    is unchanged, by construction), its publication date and its identity;
    it only adds provenance keys `head` lacks, and never overwrites one it
    has. `None` when there is nothing to add. `head` is never touched: the
    record stays append-only.
    """
    failure_reasons = validate_raw_document(document)
    if failure_reasons:
        raise ProvenanceEnrichmentRefused(f"document fails validation: {failure_reasons}")
    normalized = normalize(document)
    lineage_id = compute_lineage_id(
        provider_id=normalized.provider_id,
        source_kind=normalized.source_kind,
        company=normalized.company,
        identifier=normalized.identifier,
    )
    if lineage_id != head.lineage_id:
        raise ProvenanceEnrichmentRefused("document belongs to a different lineage")
    if normalized.content_hash != head.content_hash:
        raise ProvenanceEnrichmentRefused("content differs: a new version of the content, not an enrichment")
    # Every key `head` holds must be repeated exactly. A descriptive key only
    # the document carries (one a later adapter adds outside the content
    # hash) is no change to `head`, and is not written either.
    if any(normalized.metadata.get(k) != v for k, v in head.metadata.items() if k not in provenance_keys):
        raise ProvenanceEnrichmentRefused("non-provenance metadata differs")
    if any(k in head.metadata and head.metadata[k] != v for k, v in normalized.metadata.items() if k in provenance_keys):
        raise ProvenanceEnrichmentRefused("provenance already stored differs")
    additions = {
        k: v for k, v in normalized.metadata.items() if k in provenance_keys and k not in head.metadata
    }
    if not additions:
        return None
    version = RecordVersion(
        version_number=head.version.version_number + 1,
        created_at=evaluated_at,
        content_hash=head.content_hash,
        supersedes=head.id,
    )
    return replace(
        head,
        id=f"{lineage_id}:v{version.version_number}",
        version=version,
        metadata={**head.metadata, **additions},
        provenance=replace(head.provenance, computed_at=evaluated_at),
    )
