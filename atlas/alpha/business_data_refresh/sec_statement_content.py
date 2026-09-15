"""SEC-only statement content refresh (developer tooling): re-version the
financial statements Atlas already holds from one saved SEC companyfacts
payload -- never a quote, a profile, a filing history, or any Alpha
Vantage call.

A statement stored before an adapter learned to capture a concept (or the
filing behind its share count) differs in content from what the adapter
returns today, so `pipeline.enrich_provenance` rightly refuses it: an
enrichment may add provenance, never content. This compares each stored
statement with the adapter's document for the same lineage, strictly:

- `IDENTICAL` -- same content: only provenance may be missing, added by
  `enrich_provenance` (nothing written when there is nothing to add).
- `ADDITIONS_ONLY` -- every value the stored version holds, its period,
  publication and source repeated exactly, and only keys it lacks added:
  new filing content, ingested as a new version of the same lineage. The
  stored version is never touched; the new one keeps its identity.
- `VALUE_CHANGED` -- any stored value, key, period, publication, source or
  already-stored provenance differs, or the content differs with nothing
  added: held, never written.
- `NEW_PERIOD` -- a period Atlas holds no statement for: held.

Pure except `fetch_companyfacts` (exactly one keyless request) -- the one
place the SEC adapter is reached (`atlas.business_data_providers` has one
importer package).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_data.models import BusinessRecord, RawBusinessDocument
from atlas.analysis_engine.business_data.normalization import normalize
from atlas.analysis_engine.business_data.pipeline import (
    SHARE_COUNT_PROVENANCE_KEYS,
    IngestionRejected,
    enrich_provenance,
    ingest,
)
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import DuplicateRecord, compute_lineage_id, latest_versions
from atlas.business_data_providers.sec_edgar import _COMPANYFACTS_URL_TEMPLATE, SecEdgarFundamentalsProvider
from atlas.business_data_providers.sec_edgar_identity import SecEdgarIdentity

__all__ = [
    "ContentKind",
    "StatementComparison",
    "companyfacts_url",
    "fetch_companyfacts",
    "statement_documents",
    "compare_statements",
    "content_refresh_records",
]


class ContentKind(str, Enum):
    IDENTICAL = "identical"
    ADDITIONS_ONLY = "additions_only"
    VALUE_CHANGED = "value_changed"
    NEW_PERIOD = "new_period"


@dataclass(frozen=True)
class StatementComparison:
    identifier: str
    period_end: str | None
    kind: ContentKind
    head_id: str | None
    #: Keys the stored version lacks (content), and provenance it lacks.
    added: tuple[str, ...] = ()
    provenance_added: tuple[str, ...] = ()
    #: (field, stored, now) for every stored value that differs or is gone.
    changed: tuple[tuple[str, object, object], ...] = ()

    @property
    def writes(self) -> bool:
        return self.kind is ContentKind.ADDITIONS_ONLY or (self.kind is ContentKind.IDENTICAL and bool(self.provenance_added))


def companyfacts_url(cik10: str) -> str:
    return _COMPANYFACTS_URL_TEMPLATE.format(cik10=cik10)


def fetch_companyfacts(cik10: str, *, fetch_json_fn=None, on_request=None) -> object:
    """Exactly one keyless SEC request: companyfacts for a CIK Atlas already
    holds (no ticker map)."""
    identity = SecEdgarIdentity(fetch_json_fn, ticker_cik_map={})
    if on_request is not None:
        on_request()
    return identity.fetch_json(companyfacts_url(cik10))


def statement_documents(ticker: str, cik10: str, payload: object) -> tuple[RawBusinessDocument, ...]:
    """The production SEC adapter's statements for `ticker`, from a saved
    companyfacts payload -- offline: any other URL is refused."""
    url = companyfacts_url(cik10)

    def saved(requested: str, headers) -> object:
        if requested != url:
            raise RuntimeError(f"offline: {requested} is not the saved payload")
        return payload

    provider = SecEdgarFundamentalsProvider(saved, ticker_cik_map={ticker.upper(): cik10})
    # The adapter dates nothing from the clock (its own contract).
    return provider.fetch(company_identifier=ticker, evaluated_at=datetime.min)


def _lineage(document: RawBusinessDocument) -> str:
    n = normalize(document)
    return compute_lineage_id(provider_id=n.provider_id, source_kind=n.source_kind, company=n.company, identifier=n.identifier)


def _compare(document: RawBusinessDocument, head: BusinessRecord | None) -> StatementComparison:
    n = normalize(document)
    period = n.period_end.isoformat() if n.period_end else None
    if head is None:
        return StatementComparison(n.identifier, period, ContentKind.NEW_PERIOD, None)
    changed: list[tuple[str, object, object]] = []
    for name, stored, now in (("period_start", head.period_start, n.period_start),
                              ("period_end", head.period_end, n.period_end),
                              ("published_at", head.published_at, n.published_at),
                              ("source_reference", head.source_reference, n.raw_reference)):
        if stored != now:
            changed.append((name, stored, now))
    for key, stored in sorted(head.metadata.items()):
        if key not in n.metadata:
            changed.append((key, stored, None))
        elif n.metadata[key] != stored:
            changed.append((key, stored, n.metadata[key]))
    added = tuple(sorted(k for k in n.metadata if k not in head.metadata and k not in SHARE_COUNT_PROVENANCE_KEYS))
    provenance = tuple(sorted(k for k in n.metadata if k not in head.metadata and k in SHARE_COUNT_PROVENANCE_KEYS))
    if changed:
        return StatementComparison(n.identifier, period, ContentKind.VALUE_CHANGED, head.id, added, provenance, tuple(changed))
    if n.content_hash == head.content_hash:
        return StatementComparison(n.identifier, period, ContentKind.IDENTICAL, head.id, added, provenance)
    if not added:
        # The content differs yet nothing is added: something the stored
        # values do not show changed. Held, never explained away.
        return StatementComparison(n.identifier, period, ContentKind.VALUE_CHANGED, head.id, (), provenance,
                                   (("content_hash", head.content_hash, n.content_hash),))
    return StatementComparison(n.identifier, period, ContentKind.ADDITIONS_ONLY, head.id, added, provenance)


def compare_statements(documents: tuple[RawBusinessDocument, ...], records: tuple[BusinessRecord, ...]
                       ) -> tuple[StatementComparison, ...]:
    """Each statement document against the latest stored version of its own
    lineage. Deterministic, in period order."""
    heads = {r.lineage_id: r for r in latest_versions(records) if r.document_type is SourceKind.FINANCIAL_STATEMENT}
    statements = [d for d in documents if normalize(d).source_kind is SourceKind.FINANCIAL_STATEMENT]
    return tuple(sorted((_compare(d, heads.get(_lineage(d))) for d in statements),
                        key=lambda c: (c.period_end or "", c.identifier)))


def content_refresh_records(documents: tuple[RawBusinessDocument, ...], records: tuple[BusinessRecord, ...], *,
                            evaluated_at: datetime) -> tuple[tuple[StatementComparison, BusinessRecord | None], ...]:
    """Each comparison with the record it would write (`None`: nothing).
    Additions become the lineage's next version through normal ingestion,
    carrying the superseded version's identity unchanged; identical content
    gains only missing provenance; everything held writes nothing."""
    by_lineage = {_lineage(d): d for d in documents}
    heads = {r.id: r for r in records}
    known = list(records)
    out = []
    for comparison in compare_statements(documents, records):
        record = None
        if comparison.writes:
            head = heads[comparison.head_id]
            document = by_lineage[head.lineage_id]
            if comparison.kind is ContentKind.IDENTICAL:
                record = enrich_provenance(document, head=head, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS,
                                           evaluated_at=evaluated_at)
            else:
                result = ingest(document, existing_records=tuple(known), evaluated_at=evaluated_at,
                                canonical_security_id=head.canonical_security_id,
                                resolution_version=head.resolution_version,
                                identity_resolved_at=head.identity_resolved_at,
                                provider_evidence_reference=head.provider_evidence_reference)
                if isinstance(result, (IngestionRejected, DuplicateRecord)):
                    raise RuntimeError(f"{comparison.identifier}: additions did not ingest as a new version ({result})")
                record = replace(result.record, canonical_issuer_id=head.canonical_issuer_id)
                if record.lineage_id != head.lineage_id or record.version.supersedes != head.id:
                    raise RuntimeError(f"{comparison.identifier}: not the next version of {head.id}")
        if record is not None:
            known.append(record)
        out.append((comparison, record))
    return tuple(out)
