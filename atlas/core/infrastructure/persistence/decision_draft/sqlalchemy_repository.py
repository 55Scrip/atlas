"""SQLAlchemy-backed DecisionDraftEventRepository.

`add` is the only write operation and is always an INSERT — the "no
UPDATE, ever" contract enforced at the type level by the repository
Protocol, and here simply never implemented at all.

`get_latest_event` orders by `(recorded_at DESC, id DESC)`, the
identical deterministic-tiebreak idiom
`atlas.alpha.security_confirmation.repository`'s own `get_latest_event`
already uses, reused verbatim for the same reason: two events written
"at the same instant" under an injected, fixed test clock must still
resolve to a stable order.

`list_latest_by_case` reads every event for a Case (ordered oldest
first) and reduces to the latest row per `draft_id` in Python, rather
than a SQL `GROUP BY` — the same choice `DecisionDraft-Implementation-
Design.md` §10 names explicitly as trivial at expected draft volumes
and the natural place to optimize later if that ever changes.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import asc, desc, insert, select
from sqlalchemy.engine import Engine

from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.value_objects import UserId
from atlas.core.domain.decision_draft.entity import DecisionDraftEvent
from atlas.core.domain.decision_draft.value_objects import DraftId
from atlas.core.infrastructure.persistence.decision_draft.table import decision_draft_events_table

__all__ = ["SqlAlchemyDecisionDraftEventRepository"]


class SqlAlchemyDecisionDraftEventRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, event: DecisionDraftEvent) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(decision_draft_events_table).values(**_to_row(event)))

    def get_latest_event(self, draft_id: DraftId) -> DecisionDraftEvent | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(decision_draft_events_table)
                    .where(decision_draft_events_table.c.draft_id == str(draft_id))
                    .order_by(
                        desc(decision_draft_events_table.c.recorded_at),
                        desc(decision_draft_events_table.c.id),
                    )
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_event(row) if row is not None else None

    def list_events(self, draft_id: DraftId) -> list[DecisionDraftEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(decision_draft_events_table)
                    .where(decision_draft_events_table.c.draft_id == str(draft_id))
                    .order_by(
                        asc(decision_draft_events_table.c.recorded_at),
                        asc(decision_draft_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )
        return [_to_event(row) for row in rows]

    def list_latest_by_case(self, case_id: CaseId) -> list[DecisionDraftEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(decision_draft_events_table)
                    .where(decision_draft_events_table.c.case_id == str(case_id))
                    .order_by(
                        asc(decision_draft_events_table.c.recorded_at),
                        asc(decision_draft_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )

        latest_by_draft_id: dict[str, DecisionDraftEvent] = {}
        for row in rows:
            event = _to_event(row)
            latest_by_draft_id[str(event.draft_id)] = event  # later rows overwrite earlier ones
        return list(latest_by_draft_id.values())

    def list_latest_by_user(self, user_id: UserId) -> list[DecisionDraftEvent]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(decision_draft_events_table)
                    .where(decision_draft_events_table.c.user_id == str(user_id))
                    .order_by(
                        asc(decision_draft_events_table.c.recorded_at),
                        asc(decision_draft_events_table.c.id),
                    )
                )
                .mappings()
                .all()
            )

        latest_by_draft_id: dict[str, DecisionDraftEvent] = {}
        for row in rows:
            event = _to_event(row)
            latest_by_draft_id[str(event.draft_id)] = event  # later rows overwrite earlier ones
        return list(latest_by_draft_id.values())


def _to_row(event: DecisionDraftEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "draft_id": str(event.draft_id),
        "case_id": str(event.case_id),
        "user_id": str(event.user_id),
        "event_type": event.event_type,
        "decision_type": event.decision_type,
        "subject": event.subject,
        "reason": event.reason,
        "confidence": event.confidence,
        "decided_at": event.decided_at.isoformat() if event.decided_at is not None else None,
        "source": event.source,
        "situation": event.situation,
        "portfolio_relevance": event.portfolio_relevance,
        "capital_considerations": event.capital_considerations,
        "alternatives_considered": json.dumps(list(event.alternatives_considered)),
        "uncertainties": json.dumps(list(event.uncertainties)),
        "committed_decision_id": event.committed_decision_id,
        "recorded_at": event.recorded_at.isoformat(),
    }


def _to_event(row: Mapping[str, Any]) -> DecisionDraftEvent:
    return DecisionDraftEvent(
        id=row["id"],
        draft_id=DraftId(uuid.UUID(row["draft_id"])),
        case_id=CaseId(uuid.UUID(row["case_id"])),
        user_id=UserId(uuid.UUID(row["user_id"])),
        event_type=row["event_type"],
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
        decision_type=row["decision_type"],
        subject=row["subject"],
        reason=row["reason"],
        confidence=row["confidence"],
        decided_at=datetime.fromisoformat(row["decided_at"]) if row["decided_at"] else None,
        source=row["source"],
        situation=row["situation"],
        portfolio_relevance=row["portfolio_relevance"],
        capital_considerations=row["capital_considerations"],
        alternatives_considered=tuple(json.loads(row["alternatives_considered"]))
        if row["alternatives_considered"]
        else (),
        uncertainties=tuple(json.loads(row["uncertainties"])) if row["uncertainties"] else (),
        committed_decision_id=row["committed_decision_id"],
    )
