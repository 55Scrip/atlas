"""Versioning (ATLAS-022, Phase 8) -- immutable version history for
Business Records.

**A `BusinessRecord` is never mutated or overwritten.** Republishing a
document produces a wholly new `BusinessRecord` whose
`version.supersedes` points *backward* at the previous version's `id`.
"Which version is current" is therefore always a derived fact computed
over a collection (`latest_versions`), never a field flipped on the old
record -- the old record stays exactly as constructed, forever, which
is what "immutable" and "preserve history" both require simultaneously.

`lineage_id` is the stable identity that groups every version of what
is logically the same document (Phase 8's "if a provider republishes a
filing, create a new version"). It is computed once, deterministically,
from the fields that identify *which document this is* -- provider,
source kind, company, and the provider's own document identifier --
never from `content_hash` (which is expected to *change* between
versions; that is precisely what makes a new version new).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_data.exceptions import BusinessDataContractError
from atlas.analysis_engine.business_data.models import BusinessRecord, RecordVersion
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["compute_lineage_id", "DuplicateRecord", "latest_versions", "determine_version"]

_LINEAGE_FIELD_SEPARATOR = "\x1f"  # ASCII unit separator -- vanishingly unlikely in real field values


def compute_lineage_id(*, provider_id: str, source_kind: SourceKind, company: str, identifier: str) -> str:
    """Deterministic: identical (provider, source kind, company,
    identifier) always produces the identical lineage id, in this
    process and any other. A `sha256` digest, not a delimited join, so
    no real-world field value can accidentally collide with the
    separator and blur two distinct lineages together."""
    raw = _LINEAGE_FIELD_SEPARATOR.join((provider_id, source_kind.value, company, identifier))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True)
class DuplicateRecord:
    """Returned by `determine_version` instead of a new `RecordVersion`
    when a normalized document's `content_hash` exactly matches the
    current head of its lineage (Phase 11's "duplicate detection").
    **Not an error** -- a provider re-fetching an unchanged filing on a
    routine poll is an expected, ordinary occurrence, not a caller
    mistake; `pipeline.ingest` returns this to its own caller as a
    distinct, named outcome rather than raising."""

    existing_record_id: str


def latest_versions(records: tuple[BusinessRecord, ...]) -> tuple[BusinessRecord, ...]:
    """Every record in `records` that no other record's
    `version.supersedes` names -- the current head of every lineage
    present in `records`, computed fresh each call, never cached or
    stored on any record itself."""
    superseded_ids = {record.version.supersedes for record in records if record.version.supersedes is not None}
    return tuple(record for record in records if record.id not in superseded_ids)


def _latest_version_for_lineage(lineage_id: str, records: tuple[BusinessRecord, ...]) -> BusinessRecord | None:
    heads = tuple(record for record in latest_versions(records) if record.lineage_id == lineage_id)
    if len(heads) > 1:
        raise BusinessDataContractError(
            f"Inconsistent version history for lineage {lineage_id!r}: "
            f"{len(heads)} un-superseded heads found, expected at most one."
        )
    return heads[0] if heads else None


def determine_version(
    *,
    lineage_id: str,
    content_hash: str,
    existing_records: tuple[BusinessRecord, ...],
    created_at: datetime,
    provider_revision: str | None = None,
) -> RecordVersion | DuplicateRecord:
    """Deterministic given `existing_records`: the same lineage state
    and the same new `content_hash` always produce the same outcome.
    `existing_records` may hold any number of unrelated lineages --
    only the ones matching `lineage_id` are considered.
    """
    current_head = _latest_version_for_lineage(lineage_id, existing_records)

    if current_head is None:
        return RecordVersion(
            version_number=1,
            created_at=created_at,
            content_hash=content_hash,
            supersedes=None,
            provider_revision=provider_revision,
        )

    if current_head.content_hash == content_hash:
        return DuplicateRecord(existing_record_id=current_head.id)

    return RecordVersion(
        version_number=current_head.version.version_number + 1,
        created_at=created_at,
        content_hash=content_hash,
        supersedes=current_head.id,
        provider_revision=provider_revision,
    )
