"""HTTP request/response schemas for the Alpha Portfolio API.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
reused here for consistency — a read-only import from `atlas.core`, not
a modification to it.
"""
from __future__ import annotations

from atlas.alpha.portfolio.models import AlphaPortfolioState
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.domains.portfolio.models import PortfolioSummary


class ImportHoldingRequest(CamelModel):
    ticker: str
    weight_percent: float
    value_absolute: float | None = None


class ImportPortfolioRequestBody(CamelModel):
    holdings: list[ImportHoldingRequest]
    cash_weight_percent: float | None = None
    cash_value_absolute: float | None = None
    preferences_notes: str | None = None


class FromScratchRequestBody(CamelModel):
    objective: str
    horizon: str
    preferences_notes: str | None = None


class HoldingView(CamelModel):
    ticker: str
    weight_percent: float
    value_absolute: float | None = None


class PortfolioView(CamelModel):
    exists: bool
    entry_mode: str | None = None
    has_absolute_values: bool = False
    holdings: list[HoldingView] = []
    cash_weight_percent: float | None = None
    cash_value_absolute: float | None = None
    total_value: float | None = None
    number_of_holdings: int = 0
    concentration_level: str | None = None
    objective: str | None = None
    horizon: str | None = None

    @classmethod
    def empty(cls) -> "PortfolioView":
        return cls(exists=False)

    @classmethod
    def from_domain(cls, state: AlphaPortfolioState, summary: PortfolioSummary) -> "PortfolioView":
        return cls(
            exists=True,
            entry_mode=state.entry_mode.value,
            has_absolute_values=state.has_absolute_values,
            holdings=[
                HoldingView(
                    ticker=holding.ticker,
                    weight_percent=holding.weight_percent,
                    value_absolute=holding.value_absolute,
                )
                for holding in state.holdings
            ],
            cash_weight_percent=state.cash_weight_percent,
            cash_value_absolute=state.cash_value_absolute,
            # Only a meaningful currency figure when every holding and
            # cash carry a real absolute value — otherwise this stays
            # None rather than presenting a fabricated total (PFINV-008
            # Honest Incompleteness).
            total_value=summary.total_value if state.has_absolute_values else None,
            # Real, investor-supplied holdings only -- `summary` itself
            # additionally counts the synthetic CASH line `projection.py`
            # adds so the calculation engine can compute cash weight;
            # that synthetic line must never be presented as a holding.
            number_of_holdings=len(state.holdings),
            concentration_level=summary.concentration.level.value,
            objective=state.objective,
            horizon=state.horizon,
        )
