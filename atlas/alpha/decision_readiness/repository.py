"""SQLAlchemy-backed read-model cache for `DecisionReadiness`. One row
per `case_id`, upserted -- mirrors `atlas.alpha.ingestion.repository
.SqlAlchemyIngestionResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.decision_readiness.models import (
    DecisionBlocker,
    DecisionBlockerKind,
    DecisionReadiness,
    DecisionReadinessReason,
    DecisionReadinessReasonKind,
    DecisionReadinessStatus,
)
from atlas.alpha.decision_readiness.table import decision_readiness_result_table
from atlas.analysis_engine.methodology import comparable_payload, stamp_methodology

__all__ = ["SqlAlchemyDecisionReadinessResultRepository"]


def _blocker_payload(blocker: DecisionBlocker) -> dict:
    return {"kind": blocker.kind.value, "detail": blocker.detail}


def _to_blocker(payload: dict) -> DecisionBlocker:
    return DecisionBlocker(kind=DecisionBlockerKind(payload["kind"]), detail=payload["detail"])


def _reason_payload(reason: DecisionReadinessReason) -> dict:
    return {"kind": reason.kind.value, "detail": reason.detail}


def _to_reason(payload: dict) -> DecisionReadinessReason:
    return DecisionReadinessReason(kind=DecisionReadinessReasonKind(payload["kind"]), detail=payload["detail"])


def _result_payload(readiness: DecisionReadiness) -> dict:
    return {
        "caseId": readiness.case_id,
        "status": readiness.status.value,
        "blockers": [_blocker_payload(b) for b in readiness.blockers],
        "supportingReasons": [_reason_payload(r) for r in readiness.supporting_reasons],
        "generatedAt": readiness.generated_at.isoformat(),
    }


def _to_readiness(payload: dict) -> DecisionReadiness:
    return DecisionReadiness(
        case_id=payload["caseId"],
        status=DecisionReadinessStatus(payload["status"]),
        blockers=tuple(_to_blocker(b) for b in payload["blockers"]),
        supporting_reasons=tuple(_to_reason(r) for r in payload["supportingReasons"]),
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyDecisionReadinessResultRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, readiness: DecisionReadiness, *, ticker: str | None) -> None:
        payload = json.dumps(stamp_methodology(_result_payload(readiness)))
        with self._engine.begin() as connection:
            connection.execute(
                delete(decision_readiness_result_table).where(decision_readiness_result_table.c.case_id == readiness.case_id)
            )
            connection.execute(
                insert(decision_readiness_result_table).values(
                    case_id=readiness.case_id,
                    ticker=ticker,
                    generated_at=readiness.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> DecisionReadiness | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decision_readiness_result_table).where(decision_readiness_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        return _to_readiness(json.loads(row["result_json"])) if row is not None else None

    def get_comparable(self, case_id: str) -> DecisionReadiness | None:
        """The stored result, when it was written under today's analysis
        methodology -- the only previous result a change may be detected
        against (`atlas.analysis_engine.methodology`). `None` otherwise."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decision_readiness_result_table).where(decision_readiness_result_table.c.case_id == case_id)
                )
                .mappings()
                .first()
            )
        payload = comparable_payload(row["result_json"]) if row is not None else None
        return _to_readiness(payload) if payload is not None else None

    def list_all(self) -> tuple[DecisionReadiness, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(decision_readiness_result_table)).mappings().all()
        return tuple(_to_readiness(json.loads(row["result_json"])) for row in rows)
