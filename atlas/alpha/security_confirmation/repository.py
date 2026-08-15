"""SQLAlchemy-backed store for `ConfirmedSecuritySelection`.

`get_by_decision_id` returns at most one row. This is safe under v1's
own write contract (`service.py` never inserts a second row for a
`decision_id` that already has one -- a same-ticker resubmission
reuses the existing row, a different-ticker resubmission is rejected
before reaching this repository at all) rather than something this
repository itself enforces or assumes generally.
"""
from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.security_confirmation.models import ConfirmedSecuritySelection
from atlas.alpha.security_confirmation.table import security_confirmations_table

__all__ = ["SqlAlchemySecurityConfirmationRepository"]


class SqlAlchemySecurityConfirmationRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, selection: ConfirmedSecuritySelection) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(security_confirmations_table).values(**_to_row(selection)))

    def get_by_decision_id(self, decision_id: str) -> ConfirmedSecuritySelection | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(security_confirmations_table).where(
                        security_confirmations_table.c.decision_id == decision_id
                    )
                )
                .mappings()
                .first()
            )
        return _to_selection(row) if row is not None else None


def _to_row(selection: ConfirmedSecuritySelection) -> dict[str, Any]:
    return {
        "id": selection.id,
        "decision_id": selection.decision_id,
        "confirmed_ticker": selection.confirmed_ticker,
        "confirmed_display_name": selection.confirmed_display_name,
        "confirmed_cik": selection.confirmed_cik,
        "discovery_method": selection.discovery_method,
        "discovery_source": selection.discovery_source,
        "confirmed_at": selection.confirmed_at.isoformat(),
    }


def _to_selection(row: Mapping[str, Any]) -> ConfirmedSecuritySelection:
    from datetime import datetime

    return ConfirmedSecuritySelection(
        id=row["id"],
        decision_id=row["decision_id"],
        confirmed_ticker=row["confirmed_ticker"],
        confirmed_display_name=row["confirmed_display_name"],
        confirmed_cik=row["confirmed_cik"],
        discovery_method=row["discovery_method"],
        discovery_source=row["discovery_source"],
        confirmed_at=datetime.fromisoformat(row["confirmed_at"]),
    )
