"""SQLAlchemy-backed persistence for `LifecycleSnapshot`. One row per
`case_id`, upserted -- mirrors `atlas.alpha.decision_readiness
.repository.SqlAlchemyDecisionReadinessResultRepository` exactly.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.investment_case_lifecycle.models import (
    LifecycleSnapshot,
    LifecycleState,
    MandatoryCoreAssessment,
    MandatoryItemAssessment,
    MandatoryItemId,
    MissingReasonCode,
)
from atlas.alpha.investment_case_lifecycle.table import investment_case_lifecycle_history_table

__all__ = ["SqlAlchemyLifecycleSnapshotRepository"]


def _item_payload(item: MandatoryItemAssessment) -> dict:
    return {
        "item": item.item.value,
        "satisfied": item.satisfied,
        "satisfiedVia": item.satisfied_via,
        "reason": item.reason.value if item.reason is not None else None,
    }


def _to_item(payload: dict) -> MandatoryItemAssessment:
    return MandatoryItemAssessment(
        item=MandatoryItemId(payload["item"]),
        satisfied=payload["satisfied"],
        satisfied_via=payload["satisfiedVia"],
        reason=MissingReasonCode(payload["reason"]) if payload["reason"] is not None else None,
    )


def _core_payload(core: MandatoryCoreAssessment) -> dict:
    return {
        "items": [_item_payload(i) for i in core.items],
        "allSatisfied": core.all_satisfied,
    }


def _to_core(payload: dict) -> MandatoryCoreAssessment:
    return MandatoryCoreAssessment(
        items=tuple(_to_item(i) for i in payload["items"]),
        all_satisfied=payload["allSatisfied"],
    )


def _snapshot_payload(snapshot: LifecycleSnapshot) -> dict:
    return {
        "caseId": snapshot.case_id,
        "lifecycleState": snapshot.lifecycle_state.value,
        "mandatoryCore": _core_payload(snapshot.mandatory_core),
        "publishedSince": snapshot.published_since.isoformat() if snapshot.published_since is not None else None,
        "generatedAt": snapshot.generated_at.isoformat(),
    }


def _to_snapshot(payload: dict) -> LifecycleSnapshot:
    return LifecycleSnapshot(
        case_id=payload["caseId"],
        lifecycle_state=LifecycleState(payload["lifecycleState"]),
        mandatory_core=_to_core(payload["mandatoryCore"]),
        published_since=datetime.fromisoformat(payload["publishedSince"]) if payload["publishedSince"] is not None else None,
        generated_at=datetime.fromisoformat(payload["generatedAt"]),
    )


class SqlAlchemyLifecycleSnapshotRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert(self, snapshot: LifecycleSnapshot, *, ticker: str | None) -> None:
        payload = json.dumps(_snapshot_payload(snapshot))
        with self._engine.begin() as connection:
            connection.execute(
                delete(investment_case_lifecycle_history_table).where(
                    investment_case_lifecycle_history_table.c.case_id == snapshot.case_id
                )
            )
            connection.execute(
                insert(investment_case_lifecycle_history_table).values(
                    case_id=snapshot.case_id,
                    ticker=ticker,
                    generated_at=snapshot.generated_at.isoformat(),
                    result_json=payload,
                )
            )

    def get(self, case_id: str) -> LifecycleSnapshot | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(investment_case_lifecycle_history_table).where(
                        investment_case_lifecycle_history_table.c.case_id == case_id
                    )
                )
                .mappings()
                .first()
            )
        return _to_snapshot(json.loads(row["result_json"])) if row is not None else None

    def list_all(self) -> tuple[LifecycleSnapshot, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(select(investment_case_lifecycle_history_table)).mappings().all()
        return tuple(_to_snapshot(json.loads(row["result_json"])) for row in rows)
