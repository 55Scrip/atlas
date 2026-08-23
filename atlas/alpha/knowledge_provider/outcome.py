"""Per-run provider outcome reporting (Automatic Knowledge Ingestion
Framework, Phase 1/3).

`summarize_acquisition` is a pure classifier over an already-computed
`RefreshSummary` (`atlas.alpha.business_data_refresh.refresh_company_data`'s
own return value) -- it fetches, validates, and versions nothing
itself; that already happened, exactly once, inside `pipeline.ingest`/
`versioning.determine_version`. Mirrors the shape of `atlas.alpha
.ingestion.engine.classify_refresh` (also a pure `RefreshSummary`
classifier) rather than inventing a second, competing pattern.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.business_data_refresh.models import RefreshSummary
from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.alpha.knowledge_provider.contract import KnowledgeProvider

__all__ = ["ExtractionStatus", "AcquisitionValidationStatus", "KnowledgeAcquisitionOutcome", "summarize_acquisition"]


class ExtractionStatus(str, Enum):
    """Whether this run actually produced new knowledge -- reused
    verbatim from `RefreshSummary.changed_records`'s own real counts,
    never re-derived or guessed."""

    COMPLETE = "complete"
    """At least one document was fetched and at least one new/updated
    `BusinessRecord` was written -- no provider error at all."""
    PARTIAL = "partial"
    """Some real progress happened (new/updated records), but at least
    one provider error was also recorded this run."""
    FAILED = "failed"
    """A provider error was recorded and no new/updated record was
    written -- this run learned nothing new."""
    NO_DATA = "no_data"
    """No provider error, but nothing new either -- an honest "checked,
    nothing changed," never conflated with `FAILED`."""


class AcquisitionValidationStatus(str, Enum):
    """A run-level rollup of `pipeline.ingest`'s own per-document
    validation outcomes (`IngestedRecord`/`IngestionRejected`/
    `DuplicateRecord`) -- distinct from `BusinessRecord.validation_status`
    (always `VALID` by construction, since a rejected document never
    becomes a `BusinessRecord` at all); this classifies the *run*, not
    one record."""

    ALL_VALID = "all_valid"
    """Every fetched document became a real `BusinessRecord` (new,
    updated, or an exact duplicate of one already known) -- zero
    rejections."""
    PARTIALLY_VALID = "partially_valid"
    """At least one document was rejected by `validate_raw_document`,
    but at least one other became a real `BusinessRecord`."""
    ALL_REJECTED = "all_rejected"
    """Every fetched document was rejected -- a real, checked provider-
    contract mismatch, never silently downgraded to `NO_DATA`."""
    NOT_APPLICABLE = "not_applicable"
    """Nothing was fetched this run at all (e.g. the provider raised
    before returning any document, or genuinely found none)."""


@dataclass(frozen=True)
class KnowledgeAcquisitionOutcome:
    """The Phase 1/3 answer to "what happened when this provider ran,
    and can it be trusted" -- every field read straight off an
    already-computed `RefreshSummary`, never a new judgment."""

    provider_id: str
    supported_domains: tuple[KnowledgeDomain, ...]
    collected_at: datetime
    extraction_status: ExtractionStatus
    validation_status: AcquisitionValidationStatus
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    confidence: float | None
    """`None` for every provider today -- every current `KnowledgeProvider`
    (SEC EDGAR) is a primary, authoritative source with no heuristic
    extraction step to grade; reserved for a future provider whose own
    extraction genuinely has a gradient of certainty (e.g. an AI
    extraction agent), never fabricated for a provider that doesn't."""
    fetched_documents: int
    new_records: int
    new_versions: int
    duplicates_skipped: int
    rejected_documents: int


def summarize_acquisition(
    provider: KnowledgeProvider, summary: RefreshSummary, *, evaluated_at: datetime
) -> KnowledgeAcquisitionOutcome:
    changed_count = summary.new_records + summary.new_versions
    has_errors = len(summary.provider_errors) > 0

    if changed_count > 0 and not has_errors:
        extraction_status = ExtractionStatus.COMPLETE
    elif changed_count > 0 and has_errors:
        extraction_status = ExtractionStatus.PARTIAL
    elif has_errors:
        extraction_status = ExtractionStatus.FAILED
    else:
        extraction_status = ExtractionStatus.NO_DATA

    if summary.fetched_documents == 0:
        validation_status = AcquisitionValidationStatus.NOT_APPLICABLE
    elif summary.rejected_documents == 0:
        validation_status = AcquisitionValidationStatus.ALL_VALID
    elif summary.rejected_documents >= summary.fetched_documents:
        validation_status = AcquisitionValidationStatus.ALL_REJECTED
    else:
        validation_status = AcquisitionValidationStatus.PARTIALLY_VALID

    warnings: list[str] = []
    if summary.duplicates_skipped > 0:
        warnings.append(f"{summary.duplicates_skipped} duplicate document(s) skipped")
    if summary.rejected_documents > 0:
        warnings.append(f"{summary.rejected_documents} document(s) rejected by validation")

    return KnowledgeAcquisitionOutcome(
        provider_id=provider.provider_id,
        supported_domains=provider.supported_domains,
        collected_at=summary.evaluated_at or evaluated_at,
        extraction_status=extraction_status,
        validation_status=validation_status,
        errors=tuple(f"{failure.provider_id}: {failure.error}" for failure in summary.provider_errors),
        warnings=tuple(warnings),
        confidence=None,
        fetched_documents=summary.fetched_documents,
        new_records=summary.new_records,
        new_versions=summary.new_versions,
        duplicates_skipped=summary.duplicates_skipped,
        rejected_documents=summary.rejected_documents,
    )
