"""SQLAlchemy-backed read-model cache for `MonitoringResult` (Deliverable
21). One row per `case_id`, upserted (delete-then-insert, matching this
codebase's `AlphaPortfolioStore`-style "latest state only" persistence,
not the append-only-events pattern `evidence_timeline`/
`investment_case_change` use for their own genuine comparison history).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Engine

from atlas.alpha.daily_brief_agenda.models import AgendaItemKind
from atlas.alpha.monitoring.models import (
    MonitoringChange,
    MonitoringChangeCategory,
    MonitoringFailure,
    MonitoringMateriality,
    MonitoringResult,
    MonitoringRunRecord,
    MonitoringScope,
    MonitoringStatus,
    OperationalRunStatus,
)
from atlas.alpha.monitoring.table import monitoring_result_table, monitoring_run_record_table
from atlas.analysis_engine.investment_case_change import ChangeDirection

__all__ = ["SqlAlchemyMonitoringResultRepository", "SqlAlchemyMonitoringRunRecordRepository"]


def _change_payload(change: MonitoringChange) -> dict:
    return {
        "id": change.id,
        "category": change.category.value,
        "materiality": change.materiality.value,
        "direction": change.direction.value,
        "reason": change.reason,
        "sourceCapability": change.source_capability,
        "evidenceReference": change.evidence_reference,
    }


def _result_payload(result: MonitoringResult) -> dict:
    return {
        "caseId": result.case_id,
        "ticker": result.ticker,
        "scope": result.scope.value,
        "status": result.status.value,
        "changes": [_change_payload(c) for c in result.changes],
        "stanceLevel": result.stance_level,
        "confidenceLevel": result.confidence_level,
        "coverageLevel": result.coverage_level,
        "latestMeaningfulEvidenceAt": result.latest_meaningful_evidence_at.isoformat()
        if result.latest_meaningful_evidence_at is not None
        else None,
        "recommendedAction": result.recommended_action.value if result.recommended_action is not None else None,
        "generatedAt": result.generated_at.isoformat(),
    }


def _to_result(payload: dict) -> MonitoringResult:
    return MonitoringResult(
        case_id=payload["caseId"],
        ticker=payload["ticker"],
        scope=MonitoringScope(payload["scope"]),
        status=MonitoringStatus(payload["status"]),
        changes=tuple(
            MonitoringChange(
                id=c["id"],
                category=MonitoringChangeCategory(c["category"]),
                materiality=MonitoringMateriality(c["materiality"]),
                direction=ChangeDirection(c["direction"]),
                reason=c["reason"],
                source_capability=c["sourceCapability"],
                evidence_reference=c["evidenceReference"],
            )
            for c in payload["changes"]
        ),
        stance_level=payload["stanceLevel"],
        confidence_level=payload["confidenceLevel"],
        coverage_level=payload["coverageLevel"],
        latest_meaningful_evidence_at=datetime.fromisoformat(payload["latestMeaningfulEvidenceAt"])
        if payload["latestMeaningfulEvidenceAt"] is not None
        else None,
        recommended_action=AgendaItemKind(payload["recommendedAction"]) if payload["recommendedAction"] is not None else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyMonitoringResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, result: MonitoringResult) -> None:
        payload = json.dumps(_result_payload(result))
        with self._engine.begin() as connection:
            connection.execute(delete(monitoring_result_table).where(monitoring_result_table.c.case_id == result.case_id))
            connection.execute(
                insert(monitoring_result_table).values(
                    case_id=result.case_id,
                    ticker=result.ticker,
                    generated_at=result.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> MonitoringResult | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(monitoring_result_table).where(monitoring_result_table.c.case_id == case_id))
                .mappings()
                .first()
            )
        return _to_result(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[MonitoringResult, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(monitoring_result_table)).mappings().all()
        return tuple(_to_result(json.loads(row["result_json"])) for row in rows)


def _failure_payload(failure: MonitoringFailure) -> dict:
    return {"caseId": failure.case_id, "ticker": failure.ticker, "error": failure.error}


def _to_failure(payload: dict) -> MonitoringFailure:
    return MonitoringFailure(case_id=payload["caseId"], ticker=payload["ticker"], error=payload["error"])


def _to_run_record(row) -> MonitoringRunRecord:
    return MonitoringRunRecord(
        run_id=row["run_id"],
        status=OperationalRunStatus(row["status"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] is not None else None,
        forced=row["forced"] == "true",
        evaluated_count=int(row["evaluated_count"]),
        skipped_count=int(row["skipped_count"]),
        failures=tuple(_to_failure(f) for f in json.loads(row["failures_json"])),
    )


class SqlAlchemyMonitoringRunRecordRepository:
    """Append-only: `start()` writes exactly one row per real
    `MonitoringService.run()` call; `complete()` updates that same row
    once, at the end. Never a second row for one run, never a second
    `complete()` for the same `run_id`."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def start(self, *, forced: bool) -> MonitoringRunRecord:
        record = MonitoringRunRecord(
            run_id=str(uuid.uuid4()),
            status=OperationalRunStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            forced=forced,
            evaluated_count=0,
            skipped_count=0,
            failures=(),
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(monitoring_run_record_table).values(
                    run_id=record.run_id,
                    status=record.status.value,
                    started_at=record.started_at.isoformat(),
                    completed_at=None,
                    forced="true" if forced else "false",
                    evaluated_count="0",
                    skipped_count="0",
                    failures_json="[]",
                )
            )
        return record

    def complete(
        self, run_id: str, *, evaluated_count: int, skipped_count: int, failures: tuple[MonitoringFailure, ...]
    ) -> MonitoringRunRecord:
        completed_at = datetime.now(timezone.utc)
        status = OperationalRunStatus.FAILED if failures else OperationalRunStatus.COMPLETED
        with self._engine.begin() as connection:
            connection.execute(
                update(monitoring_run_record_table)
                .where(monitoring_run_record_table.c.run_id == run_id)
                .values(
                    status=status.value,
                    completed_at=completed_at.isoformat(),
                    evaluated_count=str(evaluated_count),
                    skipped_count=str(skipped_count),
                    failures_json=json.dumps([_failure_payload(f) for f in failures]),
                )
            )
        record = self.get(run_id)
        assert record is not None  # the row was just written by `start()`.
        return record

    def get(self, run_id: str) -> MonitoringRunRecord | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(monitoring_run_record_table).where(monitoring_run_record_table.c.run_id == run_id))
                .mappings()
                .first()
            )
        return _to_run_record(row) if row is not None else None

    def get_latest(self) -> MonitoringRunRecord | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(monitoring_run_record_table).order_by(monitoring_run_record_table.c.started_at.desc()).limit(1)
                )
                .mappings()
                .first()
            )
        return _to_run_record(row) if row is not None else None
