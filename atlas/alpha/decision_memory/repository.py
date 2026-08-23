"""SQLAlchemy-backed append-only store for `DecisionSnapshot`s and each
row's own persisted `DecisionMemoryChange` transition. Mirrors `atlas.alpha
.investment_case_change.repository.SqlAlchemyInvestmentCaseSnapshotRepository`
exactly.

`get_latest`/`get_previous` are the two reads a caller needs for the
*current* Decision Memory view. `get_history` is the third: every row
for a Case, oldest first, each paired with the `DecisionMemoryChange` that
produced it -- reconstructed from persisted columns, never recomputed
(the one exception is the first row, whose baseline `DecisionMemoryChange` is
never persisted at all -- see `table.py`'s own docstring -- and is
instead rebuilt via `detect_decision_change(None, snapshot)`, the same
pure, constant baseline constructor `investment_case_change`'s own
`compare_snapshots(None, snapshot)` already establishes as the correct
non-recomputation for this exact case).

`add` is the only write and is **idempotent by content**: it re-checks
the current head's own `content_hash` before inserting, so a caller may
call it unconditionally after every fresh assessment without ever
risking a duplicate row for structurally-unchanged state.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import asc, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.decision_memory.engine import detect_decision_change
from atlas.alpha.decision_memory.models import ChangeDirection, DecisionMemoryChange, DecisionSnapshot, DecisionTimelineEntry
from atlas.alpha.decision_memory.table import decision_memory_snapshot_table
from atlas.alpha.decision_path.models import FinalReachableState
from atlas.alpha.decision_readiness.models import DecisionReadinessStatus
from atlas.alpha.investment_decision.models import DecisionAction
from atlas.alpha.opportunity_cost.models import AlternativeKind
from atlas.alpha.recommendation_conviction.models import ConvictionStrength, RecommendationStability

__all__ = ["SqlAlchemyDecisionMemoryRepository"]


def _snapshot_payload(snapshot: DecisionSnapshot) -> dict:
    return {
        "action": snapshot.action.value,
        "readinessStatus": snapshot.readiness_status.value,
        "blockerCodes": list(snapshot.blocker_codes),
        "convictionStrength": snapshot.conviction_strength.value,
        "convictionStability": snapshot.conviction_stability.value,
        "decisionPathStepCount": snapshot.decision_path_step_count,
        "decisionPathFinalState": snapshot.decision_path_final_state.value,
        "primaryAlternativeKind": snapshot.primary_alternative_kind.value if snapshot.primary_alternative_kind is not None else None,
        "alternativeCount": snapshot.alternative_count,
    }


def _to_snapshot(row) -> DecisionSnapshot:
    payload = json.loads(row["snapshot_json"])
    return DecisionSnapshot(
        case_id=row["case_id"],
        action=DecisionAction(payload["action"]),
        readiness_status=DecisionReadinessStatus(payload["readinessStatus"]),
        blocker_codes=tuple(payload["blockerCodes"]),
        conviction_strength=ConvictionStrength(payload["convictionStrength"]),
        conviction_stability=RecommendationStability(payload["convictionStability"]),
        decision_path_step_count=payload["decisionPathStepCount"],
        decision_path_final_state=FinalReachableState(payload["decisionPathFinalState"]),
        primary_alternative_kind=AlternativeKind(payload["primaryAlternativeKind"]) if payload["primaryAlternativeKind"] is not None else None,
        alternative_count=payload["alternativeCount"],
        content_hash=row["content_hash"],
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )


def _change_payload(change: DecisionMemoryChange) -> dict:
    return {
        "previousAction": change.previous_action.value if change.previous_action is not None else None,
        "currentAction": change.current_action.value,
        "recommendationChanged": change.recommendation_changed,
        "convictionDirection": change.conviction_direction.value if change.conviction_direction is not None else None,
        "readinessDirection": change.readiness_direction.value if change.readiness_direction is not None else None,
        "decisionPathDirection": change.decision_path_direction.value if change.decision_path_direction is not None else None,
        "blockersResolved": list(change.blockers_resolved),
        "blockersAdded": list(change.blockers_added),
        "alternativeChanged": change.alternative_changed,
    }


def _to_change(payload: dict, *, case_id: str, detected_at: datetime) -> DecisionMemoryChange:
    return DecisionMemoryChange(
        case_id=case_id,
        is_baseline=False,
        previous_action=DecisionAction(payload["previousAction"]) if payload["previousAction"] is not None else None,
        current_action=DecisionAction(payload["currentAction"]),
        recommendation_changed=payload["recommendationChanged"],
        conviction_direction=ChangeDirection(payload["convictionDirection"]) if payload["convictionDirection"] is not None else None,
        readiness_direction=ChangeDirection(payload["readinessDirection"]) if payload["readinessDirection"] is not None else None,
        decision_path_direction=ChangeDirection(payload["decisionPathDirection"]) if payload["decisionPathDirection"] is not None else None,
        blockers_resolved=tuple(payload["blockersResolved"]),
        blockers_added=tuple(payload["blockersAdded"]),
        alternative_changed=payload["alternativeChanged"],
        detected_at=detected_at,
    )


class SqlAlchemyDecisionMemoryRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_latest(self, case_id: str) -> DecisionSnapshot | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decision_memory_snapshot_table)
                    .where(decision_memory_snapshot_table.c.case_id == case_id)
                    .order_by(desc(decision_memory_snapshot_table.c.recorded_at))
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_snapshot(row) if row is not None else None

    def get_previous(self, case_id: str) -> DecisionSnapshot | None:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(decision_memory_snapshot_table)
                    .where(decision_memory_snapshot_table.c.case_id == case_id)
                    .order_by(desc(decision_memory_snapshot_table.c.recorded_at))
                    .limit(2)
                )
                .mappings()
                .all()
            )
        return _to_snapshot(rows[1]) if len(rows) > 1 else None

    def get_history(self, case_id: str) -> tuple[DecisionTimelineEntry, ...]:
        """Every persisted snapshot for `case_id`, oldest first, each
        paired with the `DecisionMemoryChange` that describes how it differs
        from the row immediately before it. Read-only: never writes,
        never calls `detect_decision_change` against real prior state
        (the one exception -- the first row -- uses the pure, constant
        baseline constructor `detect_decision_change(None, snapshot)`,
        not a real comparison)."""
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(decision_memory_snapshot_table)
                    .where(decision_memory_snapshot_table.c.case_id == case_id)
                    .order_by(asc(decision_memory_snapshot_table.c.recorded_at))
                )
                .mappings()
                .all()
            )
        entries: list[DecisionTimelineEntry] = []
        for index, row in enumerate(rows):
            snapshot = _to_snapshot(row)
            if index == 0:
                change = detect_decision_change(None, snapshot, detected_at=snapshot.recorded_at)
            else:
                change = _to_change(json.loads(row["change_json"]), case_id=case_id, detected_at=snapshot.recorded_at)
            entries.append(DecisionTimelineEntry(snapshot=snapshot, change=change))
        return tuple(entries)

    def add(self, case_id: str, snapshot: DecisionSnapshot, change: DecisionMemoryChange, *, ticker: str | None) -> bool:
        """Returns `True` when a new row was actually written, `False`
        when the current head already carries an identical
        `content_hash` (structurally unchanged -- nothing is written).
        Never raises on the no-op path; a caller does not need to
        check first.

        `change` must be the exact result of `detect_decision_change`
        comparing this `snapshot` against the current head -- never
        recomputed here, and never persisted when `change.is_baseline`
        is `True` (a baseline has nothing to persist; `get_history`
        derives it structurally)."""
        current_head = self.get_latest(case_id)
        if current_head is not None and current_head.content_hash == snapshot.content_hash:
            return False
        with self._engine.begin() as connection:
            connection.execute(
                insert(decision_memory_snapshot_table).values(
                    id=f"{case_id}:{snapshot.recorded_at.isoformat()}",
                    case_id=case_id,
                    ticker=ticker,
                    recorded_at=snapshot.recorded_at.isoformat(),
                    content_hash=snapshot.content_hash,
                    snapshot_json=json.dumps(_snapshot_payload(snapshot), sort_keys=True),
                    change_json=None if change.is_baseline else json.dumps(_change_payload(change), sort_keys=True),
                )
            )
        return True
