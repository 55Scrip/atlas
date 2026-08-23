"""SQLAlchemy-backed read-model cache for `IngestionResult`. One row
per `case_id`, upserted -- mirrors `atlas.alpha.monitoring.repository
.SqlAlchemyMonitoringResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.ingestion.models import DataChange, DataChangeKind, IngestionResult
from atlas.alpha.ingestion.table import ingestion_result_table

__all__ = ["SqlAlchemyIngestionResultRepository"]


def _change_payload(change: DataChange) -> dict:
    return {
        "lineageId": change.lineage_id,
        "sourceKind": change.source_kind,
        "kind": change.kind.value,
        "recordId": change.record_id,
        "periodEnd": change.period_end,
        "detectedAt": change.detected_at.isoformat(),
    }


def _to_change(payload: dict) -> DataChange:
    return DataChange(
        lineage_id=payload["lineageId"],
        source_kind=payload["sourceKind"],
        kind=DataChangeKind(payload["kind"]),
        record_id=payload["recordId"],
        period_end=payload["periodEnd"],
        detected_at=datetime.fromisoformat(payload["detectedAt"]),
    )


def _result_payload(result: IngestionResult) -> dict:
    return {
        "ticker": result.ticker,
        "caseId": result.case_id,
        "ranAt": result.ran_at.isoformat(),
        "changes": [_change_payload(c) for c in result.changes],
        "hasNewData": result.has_new_data,
        "fetchedDocuments": result.fetched_documents,
        "duplicatesSkipped": result.duplicates_skipped,
        "rejectedDocuments": result.rejected_documents,
        "providerErrors": list(result.provider_errors),
        "identityGateOutcome": result.identity_gate_outcome,
    }


def _to_result(payload: dict) -> IngestionResult:
    return IngestionResult(
        ticker=payload["ticker"],
        case_id=payload["caseId"],
        ran_at=datetime.fromisoformat(payload["ranAt"]),
        changes=tuple(_to_change(c) for c in payload["changes"]),
        has_new_data=payload["hasNewData"],
        fetched_documents=payload["fetchedDocuments"],
        duplicates_skipped=payload["duplicatesSkipped"],
        rejected_documents=payload["rejectedDocuments"],
        provider_errors=tuple(payload["providerErrors"]),
        identity_gate_outcome=payload["identityGateOutcome"],
    )


class SqlAlchemyIngestionResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, result: IngestionResult) -> None:
        if result.case_id is None:
            return
        payload = json.dumps(_result_payload(result))
        with self._engine.begin() as connection:
            connection.execute(delete(ingestion_result_table).where(ingestion_result_table.c.case_id == result.case_id))
            connection.execute(
                insert(ingestion_result_table).values(
                    case_id=result.case_id,
                    ticker=result.ticker,
                    ran_at=result.ran_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> IngestionResult | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(ingestion_result_table).where(ingestion_result_table.c.case_id == case_id))
                .mappings()
                .first()
            )
        return _to_result(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[IngestionResult, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(ingestion_result_table)).mappings().all()
        return tuple(_to_result(json.loads(row["result_json"])) for row in rows)
