"""The canonical Business Record model (ATLAS-022, Phase 3) and its two
supporting shapes: `RawBusinessDocument` (Phase 6's "raw provider
output," before anything is checked) and `RecordVersion` (Phase 8's
immutable version marker).

**Structural information only.** No field anywhere in this module
holds a parsed financial metric, an AI-generated summary, a
recommendation, or a conclusion -- the same "facts, not judgments"
discipline `atlas.core.domain.evidence`/`observation` already establish
for investor-captured records, and `atlas.decision_engine.contracts`
already establishes for every stage result in this codebase. A
`BusinessRecord` says a document *exists*, *what kind* it is, *when* it
was published, and *where it came from* -- never what it says.

Generic enough to represent an annual report, a quarterly report, an
earnings release, an earnings call transcript, an SEC filing, a company
presentation, an investor day, a capital markets day, a news article, a
macro report, or a future document type this sprint has not named --
without a shape change. That genericity is exactly why every field
here is structural (an id, a timestamp, an enum, a hash) rather than
document-type-specific (no `revenue`, no `eps`, no `filing_number`):
document-type-specific detail belongs to whatever eventually reads
`source_reference` and interprets the real content, a capability this
sprint deliberately does not build (see `pipeline.py`'s own module
docstring).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from types import MappingProxyType
from typing import Mapping

from atlas.analysis_engine.business_data.contracts import ValidationStatus
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.provenance import Provenance

__all__ = ["RawBusinessDocument", "RecordVersion", "BusinessRecord"]

_MetadataValue = str | int | float | bool | None


def _freeze_metadata(value: Mapping[str, _MetadataValue]) -> Mapping[str, _MetadataValue]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class RawBusinessDocument:
    """Phase 6's "Raw provider output" -- exactly what a
    `providers.BusinessDataProvider` hands back, before `validation.py`
    has checked anything. Every field is optional here (even
    `source_kind`, `str`-typed rather than `SourceKind`-typed) precisely
    because a raw document may be missing what `validation.py` requires
    -- rejecting malformed input is `validation.py`'s job, not a
    constructor guard here. This type is never `BusinessRecord`-shaped
    and never itself handed to Business Analysis; it exists only to be
    validated and normalized.

    `raw_reference` is an opaque pointer to wherever the real document
    content lives (a URL, a file path, a blob id) -- this module never
    reads, stores, or interprets that content itself.
    """

    identifier: str | None
    company: str | None
    source_kind: str | None
    published_at: datetime | None
    provider_id: str | None
    raw_reference: str | None
    content_hash: str | None
    period_start: date | None = None
    period_end: date | None = None
    language: str | None = None
    metadata: Mapping[str, _MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class RecordVersion:
    """Phase 8's immutable version marker. `supersedes` points
    *backward* to the previous version's `BusinessRecord.id` in the
    same lineage, if any -- deliberately one-directional. A record is
    never mutated to point forward at whatever superseded it (that
    would require rewriting an already-constructed, already-immutable
    object); "is this the latest version" is instead a derived fact a
    caller computes over a collection (see
    `versioning.latest_versions`), never a stored field on the old
    record.
    """

    version_number: int
    created_at: datetime
    content_hash: str
    supersedes: str | None = None
    provider_revision: str | None = None

    def __post_init__(self) -> None:
        from atlas.analysis_engine.business_data.exceptions import BusinessDataContractError

        if self.version_number < 1:
            raise BusinessDataContractError("RecordVersion.version_number must be >= 1.")
        if self.version_number == 1 and self.supersedes is not None:
            raise BusinessDataContractError(
                "RecordVersion.version_number == 1 must not carry a supersedes reference "
                "-- there is no prior version in the lineage to point to."
            )
        if self.version_number > 1 and self.supersedes is None:
            raise BusinessDataContractError(
                "RecordVersion.version_number > 1 must carry a supersedes reference "
                "naming the prior version it replaces."
            )


@dataclass(frozen=True)
class BusinessRecord:
    """The canonical Business Record (Phase 3). Assembled exactly once,
    by `pipeline.ingest`, from an already-validated, already-normalized
    `RawBusinessDocument` plus a computed `RecordVersion` -- never
    constructed directly by a provider or by Business Analysis.

    `id` is deterministic and stable for one specific version of one
    specific document (`f"{lineage_id}:v{version.version_number}"`);
    `lineage_id` is stable *across* republished versions of what is
    logically the same document -- the field `versioning.py` groups by
    to decide whether a new raw document is a new version of something
    already seen or a wholly new document.

    `validation_status` is always `ValidationStatus.VALID` here (see
    that enum's own docstring for why) -- a `BusinessRecord` failing
    validation is a contradiction in terms; failed validation produces
    a `validation.ValidationRejection`, never this type.
    """

    id: str
    lineage_id: str
    identifier: str
    company: str
    document_type: SourceKind
    published_at: datetime
    provider_id: str
    source_reference: str
    content_hash: str
    version: RecordVersion
    provenance: Provenance
    validation_status: ValidationStatus
    period_start: date | None = None
    period_end: date | None = None
    language: str = "unknown"
    metadata: Mapping[str, _MetadataValue] = field(default_factory=dict)
    # Sprint O Phase 8 -- identity provenance. All four fields are
    # `None` for any `BusinessRecord` created before Sprint O (no
    # migration, no retroactive backfill -- Phase 9's own "existing
    # BusinessRecords remain untouched") and for `BusinessRecord`s
    # built in tests/paths that do not route through the Identity
    # Gate. Once the gate is wired in
    # (`atlas.alpha.business_data_refresh.service.refresh_company_data`),
    # every newly-created `BusinessRecord` carries all four, since the
    # gate only ever allows creation on `AUTO_ACCEPT`. Plain
    # primitives, not a
    # `canonical_security_gate.BusinessRecordIdentityProvenance` --
    # this module never imports that package (see `pipeline.ingest`'s
    # own signature).
    canonical_security_id: str | None = None
    resolution_version: str | None = None
    identity_resolved_at: datetime | None = None
    provider_evidence_reference: str | None = None

    def __post_init__(self) -> None:
        from atlas.analysis_engine.business_data.exceptions import BusinessDataContractError

        if self.validation_status is not ValidationStatus.VALID:
            raise BusinessDataContractError(
                "BusinessRecord.validation_status must be VALID -- a record that failed "
                "validation must never be constructed as a BusinessRecord."
            )
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
