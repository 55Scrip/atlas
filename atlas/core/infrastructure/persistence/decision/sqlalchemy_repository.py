"""SQLAlchemy-backed DecisionRepository.

Implements the append-only contract literally: `add` is the only write
operation, and it is always an INSERT. There is no update method to call by
accident.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.decision.value_objects import (
    Confidence,
    DecisionId,
    DecisionSource,
    DecisionType,
    InvestmentCase,
    Subject,
    UserId,
)
from atlas.core.domain.observation.value_objects import ObservationId
from atlas.core.infrastructure.persistence.decision.table import decisions_table


class SqlAlchemyDecisionRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, decision: Decision) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(decisions_table).values(**_to_row(decision)))

    def get(self, decision_id: DecisionId) -> Decision | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decisions_table).where(decisions_table.c.id == str(decision_id))
                )
                .mappings()
                .first()
            )
        return _to_decision(row) if row is not None else None

    def list_all(self) -> list[Decision]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(select(decisions_table).order_by(decisions_table.c.recorded_at))
                .mappings()
                .all()
            )
        return [_to_decision(row) for row in rows]


def _to_row(decision: Decision) -> dict[str, Any]:
    return {
        "id": str(decision.id),
        "case_id": str(decision.case_id),
        "user_id": str(decision.user_id),
        "decision_type": decision.decision_type.value,
        "subject": decision.subject.value,
        "reason": decision.investment_case.reason,
        "confidence": decision.confidence.value,
        "decided_at": decision.decided_at.isoformat(),
        "recorded_at": decision.recorded_at.isoformat(),
        "source": decision.source.value,
        "observation_id": str(decision.observation_id)
        if decision.observation_id is not None
        else None,
    }


def _to_decision(row: Mapping[str, Any]) -> Decision:
    return Decision(
        id=DecisionId(uuid.UUID(row["id"])),
        case_id=CaseId(uuid.UUID(row["case_id"])),
        user_id=UserId(uuid.UUID(row["user_id"])),
        decision_type=DecisionType(row["decision_type"]),
        subject=Subject(row["subject"]),
        investment_case=InvestmentCase(row["reason"]),
        confidence=Confidence(row["confidence"]),
        decided_at=datetime.fromisoformat(row["decided_at"]),
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        source=DecisionSource(row["source"]),
        observation_id=ObservationId(uuid.UUID(row["observation_id"]))
        if row.get("observation_id") is not None
        else None,
    )
