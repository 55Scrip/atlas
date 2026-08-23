"""The Ingestion Engine -- pure, deterministic (Deliverable 3). Every
function here is a total function of an already-computed `RefreshSummary`
(`atlas.alpha.business_data_refresh.refresh_company_data`'s own return
value); none of them fetch, validate, or version anything themselves --
`atlas.analysis_engine.business_data.pipeline.ingest`/`versioning
.determine_version` already did that exactly once, deterministically,
per document. This module only classifies what already happened.

**Always exact, never heuristic.** `classify_refresh` reads
`RefreshSummary.changed_records` -- the real `BusinessRecord`s
`refresh_company_data` actually wrote this run, each one's own
`version.version_number` already computed by `determine_version` --
and reclassifies each into a `DataChange`. No threshold, no "looks
recent enough," no inference from `published_at` age.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from atlas.alpha.business_data_refresh.models import RefreshSummary
from atlas.alpha.ingestion.models import DataChange, DataChangeKind, IngestionResult

__all__ = ["classify_refresh", "DataFreshnessStatus", "derive_data_freshness_status"]


def _classify_record(record) -> DataChange:
    kind = DataChangeKind.NEW_DATASET if record.version.version_number == 1 else DataChangeKind.DATASET_REPLACED
    return DataChange(
        lineage_id=record.lineage_id,
        source_kind=record.document_type.value,
        kind=kind,
        record_id=record.id,
        period_end=record.period_end.isoformat() if record.period_end is not None else None,
        detected_at=record.provenance.computed_at,
    )


def classify_refresh(summary: RefreshSummary, *, ticker: str, case_id: str | None, ran_at: datetime) -> IngestionResult:
    """`ran_at` is supplied by the caller (`service.py`), never read
    from a wall clock here -- normally `summary.evaluated_at`, the same
    real timestamp `refresh_company_data` stamped onto every record it
    wrote this run (see that dataclass field's own docstring)."""
    changes = tuple(_classify_record(record) for record in summary.changed_records)
    return IngestionResult(
        ticker=ticker,
        case_id=case_id,
        ran_at=ran_at,
        changes=changes,
        has_new_data=len(changes) > 0,
        fetched_documents=summary.fetched_documents,
        duplicates_skipped=summary.duplicates_skipped,
        rejected_documents=summary.rejected_documents,
        provider_errors=tuple(f"{failure.provider_id}: {failure.error}" for failure in summary.provider_errors),
        identity_gate_outcome=summary.identity_gate_outcome,
    )


# ---------------------------------------------------------------------
# Deliverable 6/7 -- Operational Freshness, now grounded in real
# Ingestion facts rather than only Monitoring's own Decision/
# Observation/CaseCondition checkpoint (Sprint 8).
# ---------------------------------------------------------------------


class DataFreshnessStatus(str, Enum):
    """The five states Deliverable 6 requires kept "completely clear."
    Reconciles Deliverable 7's own six-item Investment Case example
    list ("New financial data available." + "Waiting for refresh.")
    into the single `WAITING_FOR_ANALYSIS` state below -- both describe
    the identical real condition (Ingestion found new data; Monitoring
    has not yet processed it) from two angles, and splitting them into
    two states would require inventing a distinction the underlying
    facts do not actually carry. See this package's own `__init__.py`
    for the full reconciliation note."""

    WAITING_FOR_NEW_DATA = "waiting_for_new_data"
    """Atlas has real, previously-ingested data for this Case, and the
    most recent check found nothing new. Deliberately not called
    "up to date" -- Atlas has no scheduler and cannot claim the world
    has not changed, only that its last check found no new dataset."""
    WAITING_FOR_ANALYSIS = "waiting_for_analysis"
    """Ingestion found genuinely new/replaced data more recently than
    Monitoring's own last successful checkpoint for this Case."""
    MONITORING_FAILED = "monitoring_failed"
    """The most recent Monitoring attempt for this specific Case
    failed (Sprint 8's own `last_run_failed_for_case`) -- takes
    priority over every other signal, since a failure is a stronger,
    more specific fact than "waiting" (mirrors `atlas.alpha.monitoring
    .engine.derive_operational_status`'s own precedence rule)."""
    NO_DATA_SOURCE = "no_data_source"
    """Ingestion has genuinely run for this ticker and every provider
    returned zero documents -- Atlas has never successfully ingested
    anything for this company, not merely "nothing new since last
    time." """
    UNKNOWN = "unknown"
    """Neither Ingestion nor Monitoring has ever produced a real result
    for this Case -- an honest absence, never defaulted to any of the
    above."""


def derive_data_freshness_status(
    ingestion_result: "IngestionResult | None",
    monitoring_checkpoint_at: datetime | None,
    *,
    last_run_failed_for_case: bool,
) -> DataFreshnessStatus:
    """Deterministic, priority-ordered -- see each branch's own
    comment. `ingestion_result` is `None` either because Ingestion has
    never run for this Case, or because this Case predates Sprint 9
    (monitored before Ingestion tracking existed) -- both are handled
    as an honest fallback, never as an error."""
    if last_run_failed_for_case:
        return DataFreshnessStatus.MONITORING_FAILED

    if ingestion_result is None:
        if monitoring_checkpoint_at is None:
            return DataFreshnessStatus.UNKNOWN
        # Monitored at least once, but Ingestion has no record for this
        # Case (pre-Sprint-9 checkpoint, or a Case never enriched
        # through a tracked path) -- honestly "we cannot say anything
        # new was detected," never "up to date."
        return DataFreshnessStatus.WAITING_FOR_NEW_DATA

    if ingestion_result.fetched_documents == 0:
        # Ingestion genuinely ran and every provider returned nothing.
        return DataFreshnessStatus.NO_DATA_SOURCE

    if monitoring_checkpoint_at is None:
        return DataFreshnessStatus.WAITING_FOR_ANALYSIS

    if ingestion_result.has_new_data and ingestion_result.ran_at > monitoring_checkpoint_at:
        return DataFreshnessStatus.WAITING_FOR_ANALYSIS

    return DataFreshnessStatus.WAITING_FOR_NEW_DATA
