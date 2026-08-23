"""HTTP response schemas for the Ingestion API. Wire format is
camelCase via the shared Core `CamelModel` (ADR-004), matching every
other Alpha schema module. Every field is a direct read of an already-
computed `IngestionResult`/`DataChange` -- nothing recomputed here.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.ingestion.models import DataChange, IngestionResult
from atlas.core.infrastructure.api.serialization import CamelModel


class DataChangeView(CamelModel):
    lineage_id: str
    source_kind: str
    kind: str
    record_id: str
    period_end: str | None
    detected_at: datetime

    @classmethod
    def from_domain(cls, change: DataChange) -> "DataChangeView":
        return cls(
            lineage_id=change.lineage_id,
            source_kind=change.source_kind,
            kind=change.kind.value,
            record_id=change.record_id,
            period_end=change.period_end,
            detected_at=change.detected_at,
        )


class IngestionResultView(CamelModel):
    ticker: str
    case_id: str | None
    ran_at: datetime
    changes: list[DataChangeView]
    has_new_data: bool
    fetched_documents: int
    duplicates_skipped: int
    rejected_documents: int
    provider_errors: list[str]
    identity_gate_outcome: str

    @classmethod
    def from_domain(cls, result: IngestionResult) -> "IngestionResultView":
        return cls(
            ticker=result.ticker,
            case_id=result.case_id,
            ran_at=result.ran_at,
            changes=[DataChangeView.from_domain(c) for c in result.changes],
            has_new_data=result.has_new_data,
            fetched_documents=result.fetched_documents,
            duplicates_skipped=result.duplicates_skipped,
            rejected_documents=result.rejected_documents,
            provider_errors=list(result.provider_errors),
            identity_gate_outcome=result.identity_gate_outcome,
        )
