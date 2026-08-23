"""Data Ingestion & Automatic Refresh (Atlas Intelligence Sprint 9).

**Deliverable 1 -- Data Source Audit, findings.** Read fresh from disk
before writing anything here:

- **Business/SEC fundamentals**
  (`atlas.analysis_engine.business_data`): contains `BusinessRecord`s,
  identity is `lineage_id` (a deterministic hash of provider + source
  kind + company + the provider's own document identifier -- never
  `content_hash`, which is expected to change between versions). New
  data is identified by `versioning.determine_version`: identical
  `content_hash` for the current lineage head -> `DuplicateRecord`
  (unchanged); different -> a real, monotonically-incrementing new
  `RecordVersion` (`version_number = current_head.version_number + 1`,
  `supersedes` naming the prior head). Full history exists (every
  version is kept, immutable, never overwritten); real version numbers
  exist; `RecordVersion.created_at` is a genuine ingestion-time
  timestamp in practice (see below) -- this is the one source that can
  drive automatic refresh detection today, and this package builds
  directly on it rather than inventing a second mechanism.
- **`RecordVersion.created_at` / `Provenance.computed_at`**: both are
  stamped from `pipeline.ingest`'s own `evaluated_at` parameter, which
  its one real production caller, `atlas.alpha.business_data_refresh
  .refresh_company_data`, sets to `datetime.now(timezone.utc)` once per
  refresh run. So this genuinely is an ingestion wall-clock timestamp
  in production -- distinct from `published_at` (the document's own
  claimed date) -- even though the pure `ingest` function itself
  treats it as just another caller-supplied parameter, not a
  dedicated, contractually-guaranteed "now" field. This package treats
  it as authoritative because its own callers are the same real
  production callers that already make that guarantee true.
- **`BusinessFact`/`ValuationFact`**: no persistence, no independent
  identity or versioning of their own -- both are recomputed fresh
  from already-persisted `BusinessRecord`s on every call. Cannot
  themselves drive dirty-detection; any signal has to come from the
  underlying `BusinessRecord`/`RecordVersion` one layer down, which is
  exactly what this package reads.
- **`atlas.alpha.business_data_refresh`**: `refresh_company_data`
  already computes, per run, exactly which `BusinessRecord`s were
  newly written (previously discarded down to bare counts in
  `RefreshSummary`) -- Sprint 9 adds one new, defaulted field
  (`RefreshSummary.changed_records`) to carry the real records through
  rather than re-deriving them. **No persisted "a refresh happened at
  time T" record existed anywhere before this sprint** (confirmed by
  exhaustive grep for `last_refresh`/`refreshed_at`/`ingested_at` --
  zero matches) -- `ingestion_results` (this package's own table) is
  the new piece that closes exactly that gap, nothing more.
- **Market/valuation snapshots**: historical snapshots carry a real,
  provider-derived `published_at` (the actual trading date) and go
  through the identical content-hash-based dedup -- usable today, no
  different from any other `BusinessRecord`. **Live/current quotes are
  a real, disclosed exception**: `published_at == evaluated_at` for a
  live quote (there being no other "publication date" concept for a
  point-in-time price), so `published_at` there already *is* the
  ingestion timestamp, not a document-claimed one -- this package does
  not attempt to separate them further for that one case, since there
  is genuinely nothing to separate.
- **Provider layer** (`atlas.business_data_providers`): confirmed no
  provider persists "last fetched at" across process runs -- both
  Alpha Vantage's and SEC EDGAR's own caches are in-memory, per-
  instance, gone at process exit. Cannot drive dirty-detection on
  their own; this package never reads provider-internal state,
  only `refresh_company_data`'s own already-public return value.
- **Ownership data**: does not exist anywhere in this codebase as a
  data source -- no model, no provider, nothing to build on. Not
  addressed by this sprint; a genuinely new source, out of scope.

**Deliverable 2 -- why this model, and not a bigger one.** Two
concepts only: `DataChange` (one real, already-versioned
`BusinessRecord`) and `IngestionResult` (one refresh call's own
summary). No `SourceUpdate`/`ObservedDataset`/`ObservedVersion`/
`SourceSnapshot` -- `BusinessRecord`/`RecordVersion` already *are* the
observed dataset and its own version history; duplicating that
ontology here would be exactly the "second parallel ingestion system"
`atlas.analysis_engine.business_data.sources.SourceKind
.MARKET_DATA_SNAPSHOT`'s own docstring already warns against for a
different case. No Core change: everything here is Alpha-only, reading
`atlas.analysis_engine.business_data`'s already-public pure functions
and `atlas.alpha.business_data_refresh`'s already-public service
functions, never modifying either package's own analytical logic.

**`DATASET_REMOVED` is deliberately not implemented.** No provider in
this codebase can assert "this document no longer exists" -- SEC EDGAR
and Alpha Vantage are both polled, stateless-per-call HTTP APIs with no
deletion feed. Implementing it would mean fabricating a fact nothing
can actually prove; documented here as an honest, disclosed gap rather
than a heuristic guess (e.g. "we haven't seen it in N refreshes, so
it's probably gone" -- exactly the kind of inference this sprint's own
"always exact, never heuristic" instruction forbids).
"""
from __future__ import annotations

from .engine import DataFreshnessStatus, classify_refresh, derive_data_freshness_status
from .models import DataChange, DataChangeKind, IngestionResult
from .service import IngestionService

__all__ = [
    "classify_refresh",
    "derive_data_freshness_status",
    "DataFreshnessStatus",
    "DataChange",
    "DataChangeKind",
    "IngestionResult",
    "IngestionService",
]
