"""Result shapes for Data Ingestion & Automatic Refresh (Atlas
Intelligence Sprint 9). See `engine.py`'s own module docstring for the
full derivation rules, and this package's `__init__.py` for the
Deliverable 1 data-source audit and Deliverable 2 model rationale.

**Smallest possible model.** Two concepts: `DataChange` (one real,
already-versioned `BusinessRecord` this refresh actually wrote) and
`IngestionResult` (one refresh call's own summary, the unit Monitoring
and the read models consume). Nothing here re-fetches, re-validates, or
re-derives anything `atlas.analysis_engine.business_data.pipeline
.ingest`/`atlas.alpha.business_data_refresh.refresh_company_data`
did not already compute.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = ["DataChangeKind", "DataChange", "IngestionResult"]


class DataChangeKind(str, Enum):
    """Deliverable 3's own closed taxonomy -- exactly the two outcomes
    `atlas.analysis_engine.business_data.versioning.determine_version`
    can produce for a document that was not a duplicate and was not
    rejected (see that function's own `RecordVersion.version_number`
    branch). `SourceKind` (already a closed, real vocabulary --
    `annual_report`/`financial_statement`/`market_data_snapshot`/etc.)
    is carried alongside on `DataChange.source_kind`, not folded into
    this enum -- this stays two members regardless of how many
    `SourceKind`s exist, the same "category plus a separate kind field"
    economy `investment_case_change.ChangeCategory`'s own docstring
    already establishes.

    **`DATASET_UNCHANGED` and `DATASET_REMOVED` are deliberately not
    members here.** An unchanged document produces no `DataChange` at
    all (nothing happened; see `IngestionResult.changes`'s own
    docstring) -- the same "never manufacture an event from a non-
    event" discipline Evidence Timeline (Sprint 6) already established.
    `DATASET_REMOVED` would require a provider-side deletion signal
    that does not exist anywhere in this codebase (confirmed by audit)
    -- implementing it would mean fabricating a fact no provider can
    actually assert; see this package's own `__init__.py`."""

    NEW_DATASET = "new_dataset"
    """`RecordVersion.version_number == 1` -- the first version ever
    seen for this lineage (Deliverable 3's "new filing"/"new financial
    statement"/"new market data", differentiated by `source_kind`)."""
    DATASET_REPLACED = "dataset_replaced"
    """`RecordVersion.version_number > 1` -- a genuine new version of
    an already-known lineage (a restatement), `RecordVersion.supersedes`
    naming the prior head."""


@dataclass(frozen=True)
class DataChange:
    """One real, already-persisted `BusinessRecord` this refresh
    actually wrote -- never a summary count, never inferred."""

    lineage_id: str
    source_kind: str
    kind: DataChangeKind
    record_id: str
    period_end: str | None
    """`BusinessRecord.period_end.isoformat()`, `None` only when the
    underlying document genuinely carries no period (e.g. a company
    profile snapshot) -- never fabricated."""
    detected_at: datetime
    """The real `evaluated_at` this refresh run used -- see
    `atlas.alpha.business_data_refresh.models.RefreshSummary
    .evaluated_at`'s own docstring for why this is a genuine wall-clock
    ingestion timestamp, not the document's own claimed publish date."""


@dataclass(frozen=True)
class IngestionResult:
    """One refresh call's own deterministic summary -- the unit
    `atlas.alpha.monitoring` consumes as one more real dirty-detection
    signal (Deliverable 5), and the unit the read models expose
    (Deliverable 6/7/8/9/10)."""

    ticker: str
    case_id: str | None
    ran_at: datetime
    changes: tuple[DataChange, ...]
    """Every genuinely new/replaced dataset this run found -- `()` on
    a run where every fetched document was either an unchanged
    duplicate or rejected; never padded with a placeholder for "nothing
    changed" (see `DataChangeKind`'s own docstring)."""
    has_new_data: bool
    """`True` iff `changes` is non-empty -- a plain derived fact,
    computed once here rather than re-checked by every caller."""
    fetched_documents: int
    duplicates_skipped: int
    rejected_documents: int
    provider_errors: tuple[str, ...]
    identity_gate_outcome: str
