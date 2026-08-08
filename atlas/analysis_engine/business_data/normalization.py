"""Normalization (ATLAS-022, Phase 6) -- the second pipeline stage,
run only on a `RawBusinessDocument` that `validation.py` has already
confirmed carries every required field.

**Deterministic structural transformation only.** Whitespace trimming,
case normalization on a hash and a language code, and converting an
already-confirmed-recognized `source_kind` string into its real
`SourceKind` member -- nothing here reads or interprets document
*content* (this module never touches `raw_reference`'s target), scores
anything, or uses an LLM. `normalize` is a pure function: identical
input always produces identical output.

`NormalizedBusinessDocument` exists as its own type, distinct from
`RawBusinessDocument`, specifically so the type system enforces Phase
6's ordering: nothing can construct a `BusinessRecord`
(`versioning.py`/`pipeline.py`) from a `RawBusinessDocument` directly --
every field that was merely `str | None` on the raw shape is a
confirmed, non-optional value here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from types import MappingProxyType
from typing import Mapping

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = ["NormalizedBusinessDocument", "normalize"]

_MetadataValue = str | int | float | bool | None


@dataclass(frozen=True)
class NormalizedBusinessDocument:
    """The output of `normalize` -- every field validation already
    confirmed present, now trimmed and case-normalized where that is a
    real structural operation (whitespace, hash casing, language-code
    casing), never a semantic one."""

    identifier: str
    company: str
    source_kind: SourceKind
    published_at: datetime
    provider_id: str
    raw_reference: str
    content_hash: str
    language: str
    period_start: date | None
    period_end: date | None
    metadata: Mapping[str, _MetadataValue]


def normalize(document: RawBusinessDocument) -> NormalizedBusinessDocument:
    """Requires `document` to have already passed
    `validation.validate_raw_document` (empty failure tuple) -- this
    function does not re-validate, matching Phase 6's fixed stage
    ordering (Validation before Normalization). Calling it on an
    unvalidated document is a caller error the type system cannot catch
    (the raw shape's fields are still merely optional); `pipeline.ingest`
    is the only caller, and only after a successful validation check.
    """
    assert document.identifier is not None
    assert document.company is not None
    assert document.source_kind is not None
    assert document.published_at is not None
    assert document.provider_id is not None
    assert document.raw_reference is not None
    assert document.content_hash is not None
    assert document.language is not None

    return NormalizedBusinessDocument(
        identifier=document.identifier.strip(),
        company=document.company.strip(),
        source_kind=SourceKind(document.source_kind),
        published_at=document.published_at,
        provider_id=document.provider_id.strip(),
        raw_reference=document.raw_reference.strip(),
        content_hash=document.content_hash.strip().lower(),
        language=document.language.strip().lower(),
        period_start=document.period_start,
        period_end=document.period_end,
        metadata=MappingProxyType(dict(document.metadata)),
    )
