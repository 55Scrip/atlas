"""Persistence for Atlas Alpha's provisional external-trade log.

Insert + read only -- no update, no delete, matching the historical,
append-only nature of a confirmed execution record. See
`atlas/alpha/portfolio/__init__.py` for this module's provisional
boundary.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio.models import AlphaTradeLogEntry, TransactionType
from atlas.alpha.portfolio.trade_log_table import alpha_trade_log_table


class AlphaTradeLogStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, entry: AlphaTradeLogEntry) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(alpha_trade_log_table).values(**_to_row(entry)))

    def get_by_outcome_id(self, outcome_id: str) -> AlphaTradeLogEntry | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(alpha_trade_log_table).where(
                        alpha_trade_log_table.c.outcome_id == outcome_id
                    )
                )
                .mappings()
                .first()
            )
        return _to_entry(row) if row is not None else None

    def list_all(self) -> list[AlphaTradeLogEntry]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(alpha_trade_log_table).order_by(alpha_trade_log_table.c.executed_at)
                )
                .mappings()
                .all()
            )
        return [_to_entry(row) for row in rows]


def _to_row(entry: AlphaTradeLogEntry) -> dict[str, Any]:
    return {
        "outcome_id": entry.outcome_id,
        "decision_id": entry.decision_id,
        "security": entry.security,
        "transaction_type": entry.transaction_type.value,
        "quantity": entry.quantity,
        "execution_price": entry.execution_price,
        "fees": entry.fees,
        "executed_at": entry.executed_at.isoformat(),
    }


def _to_entry(row: Mapping[str, Any]) -> AlphaTradeLogEntry:
    return AlphaTradeLogEntry(
        outcome_id=row["outcome_id"],
        decision_id=row["decision_id"],
        security=row["security"],
        transaction_type=TransactionType(row["transaction_type"]),
        quantity=row["quantity"],
        execution_price=row["execution_price"],
        executed_at=datetime.fromisoformat(row["executed_at"]),
        fees=row["fees"],
    )
