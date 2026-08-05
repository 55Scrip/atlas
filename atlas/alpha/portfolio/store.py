"""Persistence for Atlas Alpha's provisional portfolio state.

Single-row store: `id=1` is the one Alpha portfolio state a running
instance holds (see `models.AlphaPortfolioState`'s own singleton
docstring). `get()`/`replace()` only — no history, no versioning; this is
provisional state, not a permanent record.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from atlas.alpha.portfolio.models import (
    AlphaHolding,
    AlphaPortfolioState,
    AlphaPreferences,
    EntryMode,
    ReconciliationStatus,
)
from atlas.alpha.portfolio.table import alpha_portfolio_state_table

_SINGLETON_ID = 1


class AlphaPortfolioStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get(self) -> AlphaPortfolioState | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(alpha_portfolio_state_table).where(
                        alpha_portfolio_state_table.c.id == _SINGLETON_ID
                    )
                )
                .mappings()
                .first()
            )
        return _to_state(row) if row is not None else None

    def replace(self, state: AlphaPortfolioState) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                delete(alpha_portfolio_state_table).where(
                    alpha_portfolio_state_table.c.id == _SINGLETON_ID
                )
            )
            connection.execute(insert(alpha_portfolio_state_table).values(**_to_row(state)))


def _to_row(state: AlphaPortfolioState) -> dict[str, Any]:
    return {
        "id": _SINGLETON_ID,
        "established_at": state.established_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "entry_mode": state.entry_mode.value,
        "holdings_json": json.dumps(
            [
                {
                    "ticker": holding.ticker,
                    "weightPercent": holding.weight_percent,
                    "valueAbsolute": holding.value_absolute,
                    "caseId": holding.case_id,
                    "reconciliationStatus": holding.reconciliation_status.value,
                }
                for holding in state.holdings
            ]
        ),
        "cash_weight_percent": state.cash_weight_percent,
        "cash_value_absolute": state.cash_value_absolute,
        "objective": state.objective,
        "horizon": state.horizon,
        "preferences_notes": state.preferences.notes,
    }


def _to_state(row: Mapping[str, Any]) -> AlphaPortfolioState:
    holdings = tuple(
        AlphaHolding(
            ticker=item["ticker"],
            weight_percent=item["weightPercent"],
            value_absolute=item.get("valueAbsolute"),
            case_id=item.get("caseId"),
            reconciliation_status=ReconciliationStatus(
                item.get("reconciliationStatus", ReconciliationStatus.NONE.value)
            ),
        )
        for item in json.loads(row["holdings_json"])
    )
    return AlphaPortfolioState(
        established_at=datetime.fromisoformat(row["established_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        entry_mode=EntryMode(row["entry_mode"]),
        holdings=holdings,
        cash_weight_percent=row["cash_weight_percent"],
        cash_value_absolute=row["cash_value_absolute"],
        objective=row["objective"],
        horizon=row["horizon"],
        preferences=AlphaPreferences(notes=row["preferences_notes"]),
    )
