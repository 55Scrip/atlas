"""Validation (ATLAS-022, Phase 7).

`validate_raw_document` is a pure function: it inspects a
`RawBusinessDocument` and returns every reason it fails, never a single
first-match reason -- a caller (or a human fixing a provider's export)
gets the complete diagnostic in one pass, not one failure at a time.

**Never silently repair.** No default is invented for a missing field
anywhere in this module -- a `RawBusinessDocument` missing its
`language` is rejected, not defaulted to `"en"`; one whose `source_kind`
string does not match any `SourceKind` member is rejected, not coerced
to `SourceKind.UNKNOWN` (a provider that means "unknown" must say so
explicitly -- `UNKNOWN` is a real, valid classification a provider
chooses, never a repair this module performs on its behalf).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["ValidationFailureReason", "ValidationRejection", "validate_raw_document"]


class ValidationFailureReason(str, Enum):
    """Phase 7's own required-field list, one member per check. A
    closed set -- never a bare string -- matching every other reason
    enum already established across this codebase
    (`atlas.decision_engine.contracts.EvidenceGapKind`,
    `atlas.analysis_engine.business.BusinessDataGapKind`)."""

    MISSING_IDENTIFIER = "missing_identifier"
    MISSING_COMPANY = "missing_company"
    MISSING_SOURCE_KIND = "missing_source_kind"
    UNRECOGNIZED_SOURCE_KIND = "unrecognized_source_kind"
    MISSING_PUBLICATION_DATE = "missing_publication_date"
    MISSING_PROVIDER = "missing_provider"
    MISSING_RAW_REFERENCE = "missing_raw_reference"
    MISSING_CONTENT_HASH = "missing_content_hash"
    MISSING_LANGUAGE = "missing_language"


@dataclass(frozen=True)
class ValidationRejection:
    """A `RawBusinessDocument` that failed validation -- carries every
    reason it failed, plus the original document for traceability. This
    type is never converted into a `BusinessRecord`; a caller that
    wants to retry must obtain a corrected `RawBusinessDocument` from
    the provider, never patch this rejection in place."""

    document: RawBusinessDocument
    reasons: tuple[ValidationFailureReason, ...]


def _is_blank(value: str | None) -> bool:
    return value is None or not value.strip()


def validate_raw_document(document: RawBusinessDocument) -> tuple[ValidationFailureReason, ...]:
    """Returns every failure reason, in the fixed order Phase 7 lists
    its own required checks -- empty tuple means the document is valid.
    Deterministic: identical input always produces identical output, no
    wall-clock read, no I/O.
    """
    reasons: list[ValidationFailureReason] = []

    if _is_blank(document.identifier):
        reasons.append(ValidationFailureReason.MISSING_IDENTIFIER)
    if _is_blank(document.company):
        reasons.append(ValidationFailureReason.MISSING_COMPANY)
    if _is_blank(document.provider_id):
        reasons.append(ValidationFailureReason.MISSING_PROVIDER)
    if _is_blank(document.source_kind):
        reasons.append(ValidationFailureReason.MISSING_SOURCE_KIND)
    elif document.source_kind not in {member.value for member in SourceKind}:
        reasons.append(ValidationFailureReason.UNRECOGNIZED_SOURCE_KIND)
    if document.published_at is None:
        reasons.append(ValidationFailureReason.MISSING_PUBLICATION_DATE)
    if _is_blank(document.raw_reference):
        reasons.append(ValidationFailureReason.MISSING_RAW_REFERENCE)
    if _is_blank(document.content_hash):
        reasons.append(ValidationFailureReason.MISSING_CONTENT_HASH)
    if _is_blank(document.language):
        reasons.append(ValidationFailureReason.MISSING_LANGUAGE)

    return tuple(reasons)
