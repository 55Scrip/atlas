"""SQLAlchemy-backed CaseConditionEventRepository (ADR-CC-001).

Mirrors `SqlAlchemyDecisionDraftEventRepository` (Sprint 9) directly:
`add` is the only write operation and is always an INSERT;
`get_latest_event` orders by `(recorded_at DESC, id DESC)`, the same
deterministic tiebreak idiom reused a fifth time in this codebase
(`security_confirmation` → `decision_draft` → here); `list_latest_by_*`
reads every event for the given scope and reduces to the latest row
per `condition_id` in Python, the same choice
`DecisionDraft-Implementation-Design.md` §10 named as trivial at
expected volumes.
"""
from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import asc, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.case_condition.entity import CaseConditionEvent
from atlas.core.domain.case_condition.value_objects import CaseConditionId
from atlas.core.domain.decision.value_objects import DecisionId
from atlas.core.infrastructure.persistence.case_condition.table import (
    case_condition_events_table,
)

__all__ = ["SqlAlchemyCaseConditionEventRepository"]


class SqlAlchemyCaseConditionEventRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, event: CaseConditionEvent) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(case_condition_events_table).values(**_to_row(event)))

    def get_latest_event(self, condition_id: CaseConditionId) -> CaseConditionEvent | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(case_condition_events_table)
                    .where(case_condition_events_table.c.condition_id == str(condition_id))
                    .order_by(
                        desc(case_condition_events_table.c.recorded_at),
                        desc(case_condition_events_table.c.id),
                    )
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_event(row) if row is not None else None

    def list_events(self, condition_id: CaseConditionId) -> list[CaseConditionEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(case_condition_events_table)
                    .where(case_condition_events_table.c.condition_id == str(condition_id))
                    .order_by(
                        asc(case_condition_events_table.c.recorded_at),
                        asc(case_condition_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return [_to_event(row) for row in rows]

    def list_latest_by_case(self, case_id: CaseId) -> list[CaseConditionEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(case_condition_events_table)
                    .where(case_condition_events_table.c.case_id == str(case_id))
                    .order_by(
                        asc(case_condition_events_table.c.recorded_at),
                        asc(case_condition_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return _latest_per_condition(rows)

    def list_latest_by_decision(self, decision_id: DecisionId) -> list[CaseConditionEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(case_condition_events_table)
                    .where(case_condition_events_table.c.decision_id == str(decision_id))
                    .order_by(
                        asc(case_condition_events_table.c.recorded_at),
                        asc(case_condition_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return _latest_per_condition(rows)


def _latest_per_condition(rows: list[Mapping[str, Any]]) -> list[CaseConditionEvent]:
    latest_by_condition_id: dict[str, CaseConditionEvent] = {}
    for row in rows:
        event = _to_event(row)
        latest_by_condition_id[str(event.condition_id)] = event  # later rows overwrite earlier
    return list(latest_by_condition_id.values())


def _to_row(event: CaseConditionEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "condition_id": str(event.condition_id),
        "case_id": str(event.case_id),
        "decision_id": str(event.decision_id) if event.decision_id is not None else None,
        "event_type": event.event_type,
        "predicate_text": event.predicate_text,
        "role": event.role,
        "authorship": event.authorship,
        "structured_kind": event.structured_kind,
        "threshold_date": (
            event.threshold_date.isoformat() if event.threshold_date is not None else None
        ),
        "threshold_metric": event.threshold_metric,
        "threshold_operator": event.threshold_operator,
        "threshold_value": event.threshold_value,
        "observed_value": event.observed_value,
        "superseded_by_condition_id": event.superseded_by_condition_id,
        "recorded_at": event.recorded_at.isoformat(),
    }


def _to_event(row: Mapping[str, Any]) -> CaseConditionEvent:
    return CaseConditionEvent(
        id=row["id"],
        condition_id=CaseConditionId(uuid.UUID(row["condition_id"])),
        case_id=CaseId(uuid.UUID(row["case_id"])),
        decision_id=DecisionId(uuid.UUID(row["decision_id"])) if row["decision_id"] else None,
        event_type=row["event_type"],
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        predicate_text=row["predicate_text"],
        role=row["role"],
        authorship=row["authorship"],
        structured_kind=row["structured_kind"],
        threshold_date=(
            datetime.fromisoformat(row["threshold_date"]) if row["threshold_date"] else None
        ),
        threshold_metric=row["threshold_metric"],
        threshold_operator=row["threshold_operator"],
        threshold_value=row["threshold_value"],
        observed_value=row["observed_value"],
        superseded_by_condition_id=row["superseded_by_condition_id"],
    )
