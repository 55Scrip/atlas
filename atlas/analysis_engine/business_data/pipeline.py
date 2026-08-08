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

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.models import BusinessRecord, RawBusinessDocument
from atlas.analysis_engine.business_data.normalization import normalize
from atlas.analysis_engine.business_data.validation import ValidationFailureReason, validate_raw_document
from atlas.analysis_engine.business_data.versioning import (
    DuplicateRecord,
    compute_lineage_id,
    determine_version,
)
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger

__all__ = ["IngestedRecord", "IngestionRejected", "IngestionResult", "ingest"]

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
    )
    return IngestedRecord(record=record)
