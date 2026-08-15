"""SQLAlchemy-backed store for the Security Confirmation lifecycle.

Sprint 22: `add` now writes one append-only `SecurityConfirmationEvent`
row (never an UPDATE, never a DELETE -- see `models.py`'s own
docstring). `get_latest_event` is the one read that determines
"current state": the single most-recently-recorded event for a
`decision_id`, `ORDER BY confirmed_at DESC` with `id` as an explicit,
deterministic tiebreak -- the same "order by timestamp, fall back to a
stable secondary key purely for determinism" idiom already established
by `atlas.core.infrastructure.persistence.outcome`'s own
`list_by_decision_id` (`(occurred_at, recorded_at, id.value)`), not a
novel pattern invented here. A row with `event_type IS NULL` predates
Sprint 22 and is read back as `"confirmed"` -- the only kind of row
that could have existed before that column did.

`get_by_decision_id` is kept, unchanged in name and return shape
(`ConfirmedSecuritySelection | None`), for `service.py`'s pre-existing
callers: it is now a thin derivation over `get_latest_event` -- `None`
if there is no event yet, or if the latest event is `"revoked"`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import desc, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.security_confirmation.models import (
    ConfirmedSecuritySelection,
    SecurityConfirmationEvent,
    SecurityConfirmationEventType,
)
from atlas.alpha.security_confirmation.table import security_confirmations_table

__all__ = ["SqlAlchemySecurityConfirmationRepository"]


class SqlAlchemySecurityConfirmationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, event: SecurityConfirmationEvent) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(security_confirmations_table).values(**_to_row(event)))

    def get_latest_event(self, decision_id: str) -> SecurityConfirmationEvent | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(security_confirmations_table)
                    .where(security_confirmations_table.c.decision_id == decision_id)
                    .order_by(
                        desc(security_confirmations_table.c.confirmed_at),
                        desc(security_confirmations_table.c.id),
                    )
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _to_event(row) if row is not None else None

    def get_by_decision_id(self, decision_id: str) -> ConfirmedSecuritySelection | None:
        latest = self.get_latest_event(decision_id)
        if latest is None or latest.event_type == "revoked":
            return None
        return ConfirmedSecuritySelection(
            id=latest.id,
            decision_id=latest.decision_id,
            confirmed_ticker=latest.confirmed_ticker,
            confirmed_display_name=latest.confirmed_display_name,
            confirmed_cik=latest.confirmed_cik,
            discovery_method=latest.discovery_method,
            discovery_source=latest.discovery_source,
            confirmed_at=latest.recorded_at,
        )


def _to_row(event: SecurityConfirmationEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "decision_id": event.decision_id,
        "confirmed_ticker": event.confirmed_ticker,
        "confirmed_display_name": event.confirmed_display_name,
        "confirmed_cik": event.confirmed_cik,
        "discovery_method": event.discovery_method,
        "discovery_source": event.discovery_source,
        "confirmed_at": event.recorded_at.isoformat(),
        "event_type": event.event_type,
    }


def _to_event(row: Mapping[str, Any]) -> SecurityConfirmationEvent:
    event_type: SecurityConfirmationEventType = "confirmed" if row["event_type"] is None else row["event_type"]
    return SecurityConfirmationEvent(
        id=row["id"],
        decision_id=row["decision_id"],
        event_type=event_type,
        confirmed_ticker=row["confirmed_ticker"],
        confirmed_display_name=row["confirmed_display_name"],
        confirmed_cik=row["confirmed_cik"],
        discovery_method=row["discovery_method"],
        discovery_source=row["discovery_source"],
        recorded_at=datetime.fromisoformat(row["confirmed_at"]),
    )
