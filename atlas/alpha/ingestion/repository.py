"""SQLAlchemy-backed read-model cache for `IngestionResult`. One row
per `case_id`, upserted -- mirrors `atlas.alpha.monitoring.repository
.SqlAlchemyMonitoringResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.models import ProviderFailure
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


def _provider_failure_payload(failure: ProviderFailure) -> dict:
    return {"providerId": failure.provider_id, "error": failure.error, "kind": failure.kind}


def _to_provider_failure(payload: dict) -> ProviderFailure:
    return ProviderFailure(provider_id=payload["providerId"], error=payload["error"], kind=payload.get("kind", ""))


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
        "providerFailures": [_provider_failure_payload(f) for f in result.provider_failures],
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
        provider_failures=tuple(_to_provider_failure(f) for f in payload.get("providerFailures", ())),
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

    def get_by_ticker(self, ticker: str) -> IngestionResult | None:
        """Automatic Enrichment Coverage, Implementation Phase 1: the
        one lookup `ensure_company_enriched`'s callers need to resolve
        `known_provider_failures` for a ticker whose `case_id` they may
        not have resolved yet (`enrich_holdings`'s own bulk, Case-
        agnostic scope).

        `case_id` is this table's own primary key, not `ticker` -- a
        ticker whose Case identity was ever re-resolved (a real,
        observed condition during this sprint's own live verification:
        multiple distinct `case_id`s persisted for the identical ticker
        string, each from a real, timestamped run) can have more than
        one row. Always returns the most recently run one (`ORDER BY
        ran_at DESC`), never an arbitrary/unordered match -- an
        unordered `.first()` here previously returned a stale row for a
        ticker whose case identity had since changed, silently
        resurrecting an out-of-date provider-failure history. Case
        identity churn itself is a pre-existing condition this sprint
        does not investigate or fix (out of scope) -- this method only
        guarantees it degrades to "read the latest," never "read an
        arbitrary one.\""""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(ingestion_result_table)
                    .where(ingestion_result_table.c.ticker == ticker)
                    .order_by(desc(ingestion_result_table.c.ran_at))
                )
                .mappings()
                .first()
            )
        return _to_result(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[IngestionResult, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(ingestion_result_table)).mappings().all()
        return tuple(_to_result(json.loads(row["result_json"])) for row in rows)
