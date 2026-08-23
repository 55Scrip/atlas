"""SQLAlchemy-backed AssumptionEventRepository (ADR-AS-001).

Mirrors `SqlAlchemyCaseConditionEventRepository` (Sprint 10) directly:
`add` is the only write operation and is always an INSERT;
`get_latest_event` orders by `(recorded_at DESC, id DESC)`, the same
deterministic tiebreak idiom reused a sixth time in this codebase
(`security_confirmation` → `decision_draft` → `case_condition` → here);
`list_latest_by_*` reads every event for the given scope and reduces
to the latest row per `assumption_id` in Python.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import asc, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.assumption.entity import AssumptionEvent
from atlas.core.domain.assumption.value_objects import AssumptionId
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.persistence.assumption.table import assumption_events_table

__all__ = ["SqlAlchemyAssumptionEventRepository"]


class SqlAlchemyAssumptionEventRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, event: AssumptionEvent) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(assumption_events_table).values(**_to_row(event)))

    def get_latest_event(self, assumption_id: AssumptionId) -> AssumptionEvent | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(assumption_events_table)
                    .where(assumption_events_table.c.assumption_id == str(assumption_id))
                    .order_by(
                        desc(assumption_events_table.c.recorded_at),
                        desc(assumption_events_table.c.id),
                    )
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_event(row) if row is not None else None

    def list_events(self, assumption_id: AssumptionId) -> list[AssumptionEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(assumption_events_table)
                    .where(assumption_events_table.c.assumption_id == str(assumption_id))
                    .order_by(
                        asc(assumption_events_table.c.recorded_at),
                        asc(assumption_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return [_to_event(row) for row in rows]

    def list_latest_by_decision(self, decision_id: DecisionId) -> list[AssumptionEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(assumption_events_table)
                    .where(assumption_events_table.c.decision_id == str(decision_id))
                    .order_by(
                        asc(assumption_events_table.c.recorded_at),
                        asc(assumption_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return _latest_per_assumption(rows)

    def list_latest_by_case(self, case_id: CaseId) -> list[AssumptionEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(assumption_events_table)
                    .where(assumption_events_table.c.case_id == str(case_id))
                    .order_by(
                        asc(assumption_events_table.c.recorded_at),
                        asc(assumption_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return _latest_per_assumption(rows)


def _latest_per_assumption(rows: list[Mapping[str, Any]]) -> list[AssumptionEvent]:
    latest_by_assumption_id: dict[str, AssumptionEvent] = {}
    for row in rows:
        event = _to_event(row)
        latest_by_assumption_id[str(event.assumption_id)] = event  # later rows overwrite earlier
    return list(latest_by_assumption_id.values())


def _to_row(event: AssumptionEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "assumption_id": str(event.assumption_id),
        "decision_id": str(event.decision_id),
        "case_id": str(event.case_id),
        "event_type": event.event_type,
        "statement": event.statement,
        "authorship": event.authorship,
        "linked_case_condition_ids": (
            json.dumps(list(event.linked_case_condition_ids))
            if event.event_type == "revised"
            else None
        ),
        "evidence_id": event.evidence_id,
        "note": event.note,
        "severity": event.severity,
        "superseded_by_assumption_id": event.superseded_by_assumption_id,
        "recorded_at": event.recorded_at.isoformat(),
    }


def _to_event(row: Mapping[str, Any]) -> AssumptionEvent:
    return AssumptionEvent(
        id=row["id"],
        assumption_id=AssumptionId(uuid.UUID(row["assumption_id"])),
        decision_id=DecisionId(uuid.UUID(row["decision_id"])),
        case_id=CaseId(uuid.UUID(row["case_id"])),
        event_type=row["event_type"],
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        statement=row["statement"],
        authorship=row["authorship"],
        linked_case_condition_ids=(
            tuple(json.loads(row["linked_case_condition_ids"]))
            if row["linked_case_condition_ids"]
            else ()
        ),
        evidence_id=row["evidence_id"],
        note=row["note"],
        severity=row["severity"],
        superseded_by_assumption_id=row["superseded_by_assumption_id"],
    )
