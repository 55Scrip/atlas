"""HTTP request/response schemas for the Alpha Portfolio API.

Wire format is camelCase via the shared Core `CamelModel` (ADR-004),
reused here for consistency — a read-only import from `atlas.core`, not
a modification to it.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from atlas.alpha.portfolio.models import AlphaPortfolioState, AlphaTradeLogEntry
from atlas.core.infrastructure.api.serialization import CamelModel
from atlas.domains.portfolio.models import PortfolioSummary


class ImportHoldingRequest(CamelModel):
    """`weight_percent` is optional: whenever `value_absolute`, or
    `quantity` and `price`, are supplied for every holding in the batch,
    weight is derived server-side rather than trusted from this field --
    see `AlphaPortfolioService._build_holdings_from_input`."""

    ticker: str
    weight_percent: float | None = None
    value_absolute: float | None = None
    quantity: float | None = None
    price: float | None = None
    currency: str | None = None


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
    quantity: float | None = None
    price: float | None = None
    currency: str | None = None
    case_id: str | None = None
    reconciliation_status: str = "NONE"


class LinkCaseRequestBody(CamelModel):
    candidate_case_id: str


class CaseLinkResponse(CamelModel):
    case_id: str


class EnrichmentScheduledView(CamelModel):
    """Internal Alpha Fix Sprint 1 (Part 1): the response for both
    `POST /alpha-portfolio/import`'s automatic trigger and the explicit
    `POST /alpha-portfolio/enrich` backfill endpoint. Enrichment runs in
    the background after this response is sent, so this view carries
    only what was scheduled -- never a fabricated per-ticker outcome
    the request itself has no way to know yet."""

    scheduled_tickers: list[str]


class ApplyTradeRequestBody(CamelModel):
    outcome_id: str
    decision_id: str
    security: str
    # ADD behaves like BUY; EXIT removes the holding outright rather
    # than reducing it (ATLAS-014) -- see `service.py::TransactionType`.
    transaction_type: Literal["BUY", "SELL", "ADD", "EXIT"]
    quantity: float
    execution_price: float
    executed_at: datetime
    fees: float | None = None


class ReconcileRequestBody(CamelModel):
    mode: Literal["UPDATE_HOLDING_WEIGHT", "REPLACE_ALLOCATION"]
    ticker: str | None = None
    weight_percent: float | None = None
    holdings: list[ImportHoldingRequest] | None = None
    cash_weight_percent: float | None = None
    cash_value_absolute: float | None = None


class TradeLogEntryView(CamelModel):
    outcome_id: str
    decision_id: str
    security: str
    transaction_type: str
    quantity: float
    execution_price: float
    fees: float | None = None
    executed_at: datetime

    @classmethod
    def from_domain(cls, entry: AlphaTradeLogEntry) -> "TradeLogEntryView":
        return cls(
            outcome_id=entry.outcome_id,
            decision_id=entry.decision_id,
            security=entry.security,
            transaction_type=entry.transaction_type.value,
            quantity=entry.quantity,
            execution_price=entry.execution_price,
            fees=entry.fees,
            executed_at=entry.executed_at,
        )


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
    awaiting_reconciliation: bool = False

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
                    quantity=holding.quantity,
                    price=holding.price,
                    currency=holding.currency,
                    case_id=holding.case_id,
                    reconciliation_status=holding.reconciliation_status.value,
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
            awaiting_reconciliation=any(
                holding.reconciliation_status.value == "AWAITING_RECONCILIATION"
                for holding in state.holdings
            ),
        )
