"""Application service for Atlas Alpha's provisional portfolio state.

Sprint 1A scope: establish state from the existing-portfolio import path
or the from-scratch path, and expose the derived view. External-trade
application is Sprint 1B (Alpha Sprint 1, Phase 4 revised plan, Decision
3) and does not exist here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.alpha.portfolio.exceptions import AlphaPortfolioValidationError
from atlas.alpha.portfolio.models import (
    AlphaHolding,
    AlphaPortfolioState,
    AlphaPreferences,
    EntryMode,
)
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.domains.portfolio.models import PortfolioSummary


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ImportHoldingInput:
    ticker: str
    weight_percent: float
    value_absolute: float | None = None


@dataclass(frozen=True)
class ImportPortfolioRequest:
    holdings: tuple[ImportHoldingInput, ...]
    cash_weight_percent: float | None = None
    cash_value_absolute: float | None = None
    preferences_notes: str | None = None


@dataclass(frozen=True)
class FromScratchRequest:
    objective: str
    horizon: str
    preferences_notes: str | None = None


class AlphaPortfolioService:
    def __init__(self, store: AlphaPortfolioStore) -> None:
        self._store = store

    def import_portfolio(self, request: ImportPortfolioRequest) -> AlphaPortfolioState:
        if not request.holdings:
            raise AlphaPortfolioValidationError(
                "An imported portfolio must include at least one holding."
            )
        try:
            holdings = tuple(
                AlphaHolding(
                    ticker=item.ticker,
                    weight_percent=item.weight_percent,
                    value_absolute=item.value_absolute,
                )
                for item in request.holdings
            )
        except ValueError as exc:
            raise AlphaPortfolioValidationError(str(exc)) from exc

        if request.cash_weight_percent is not None and request.cash_weight_percent < 0:
            raise AlphaPortfolioValidationError("cash_weight_percent must not be negative")
        if request.cash_value_absolute is not None and request.cash_value_absolute < 0:
            raise AlphaPortfolioValidationError("cash_value_absolute must not be negative")

        now = _utc_now()
        state = AlphaPortfolioState(
            established_at=now,
            updated_at=now,
            entry_mode=EntryMode.IMPORTED,
            holdings=holdings,
            cash_weight_percent=request.cash_weight_percent,
            cash_value_absolute=request.cash_value_absolute,
            preferences=AlphaPreferences(notes=request.preferences_notes),
        )
        self._store.replace(state)
        return state

    def start_from_scratch(self, request: FromScratchRequest) -> AlphaPortfolioState:
        if not request.objective or not request.objective.strip():
            raise AlphaPortfolioValidationError("objective must not be blank")
        if not request.horizon or not request.horizon.strip():
            raise AlphaPortfolioValidationError("horizon must not be blank")

        now = _utc_now()
        state = AlphaPortfolioState(
            established_at=now,
            updated_at=now,
            entry_mode=EntryMode.FROM_SCRATCH,
            holdings=(),
            objective=request.objective.strip(),
            horizon=request.horizon.strip(),
            preferences=AlphaPreferences(notes=request.preferences_notes),
        )
        self._store.replace(state)
        return state

    def get_state(self) -> AlphaPortfolioState | None:
        return self._store.get()

    def get_view(self) -> PortfolioSummary | None:
        state = self._store.get()
        if state is None:
            return None
        return derive_portfolio_view(state)
