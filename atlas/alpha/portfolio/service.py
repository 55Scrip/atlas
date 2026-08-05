"""Application service for Atlas Alpha's provisional portfolio state.

Sprint 1A: establish state from the existing-portfolio import path or
the from-scratch path, expose the derived view, and link a holding to
its Investment Case.

Sprint 1B adds external-trade application and portfolio reconciliation.
`apply_confirmed_trade` reads (never writes) Core's Outcome via
`OutcomeRepository` -- the one authorized direction ("The Alpha layer
may reference Outcome. Outcome must never reference Alpha.") -- and
writes only to this module's own provisional store and trade log. No
Core entity is ever constructed or modified here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from atlas.alpha.portfolio.exceptions import (
    AlphaHoldingNotFoundError,
    AlphaPortfolioError,
    AlphaPortfolioNotEstablishedError,
    AlphaPortfolioValidationError,
    DecisionMismatchError,
    OutcomeNotFoundForTradeError,
    TradeAlreadyAppliedError,
)
from atlas.alpha.portfolio.models import (
    AlphaHolding,
    AlphaPortfolioState,
    AlphaPreferences,
    AlphaTradeLogEntry,
    EntryMode,
    ReconciliationStatus,
    TransactionType,
)
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.trade_log_store import AlphaTradeLogStore
from atlas.core.domain.outcome.repository import OutcomeRepository
from atlas.core.domain.outcome.value_objects import OutcomeId
from atlas.domains.portfolio.calculations import holding_weight
from atlas.domains.portfolio.models import PortfolioSummary
from atlas.shared import Holding as SharedHolding
from atlas.shared import Portfolio as SharedPortfolio

_ALLOCATION_TOLERANCE = 1e-6
_CASH_TICKER = "CASH"


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


@dataclass(frozen=True)
class ApplyTradeRequest:
    outcome_id: str
    decision_id: str
    security: str
    transaction_type: TransactionType
    quantity: float
    execution_price: float
    executed_at: datetime
    fees: float | None = None


@dataclass(frozen=True)
class UpdateHoldingWeightRequest:
    ticker: str
    weight_percent: float


@dataclass(frozen=True)
class ReplaceAllocationRequest:
    holdings: tuple[ImportHoldingInput, ...]
    cash_weight_percent: float | None = None
    cash_value_absolute: float | None = None


def _validate_holdings_and_cash(
    holdings: tuple[AlphaHolding, ...],
    cash_weight_percent: float | None,
    cash_value_absolute: float | None,
) -> None:
    """Shared validation for `import_portfolio` and
    `reconcile_replace_allocation` -- duplicate tickers, cash-field
    consistency, and the total-allocation cap. Kept in one place so the
    two callers can never drift out of sync (Alpha Sprint 1B: reuse, no
    duplicated validation logic)."""
    tickers = [holding.ticker for holding in holdings]
    duplicates = sorted({ticker for ticker in tickers if tickers.count(ticker) > 1})
    if duplicates:
        raise AlphaPortfolioValidationError(
            f"Duplicate ticker(s) after normalization: {', '.join(duplicates)}"
        )

    if cash_weight_percent is not None and cash_weight_percent < 0:
        raise AlphaPortfolioValidationError("cash_weight_percent must not be negative")
    if cash_weight_percent is not None and cash_weight_percent > 100:
        raise AlphaPortfolioValidationError("cash_weight_percent must not exceed 100")
    if cash_value_absolute is not None and cash_value_absolute < 0:
        raise AlphaPortfolioValidationError("cash_value_absolute must not be negative")

    cash_weight_given = cash_weight_percent is not None
    cash_value_given = cash_value_absolute is not None
    if cash_weight_given != cash_value_given:
        raise AlphaPortfolioValidationError(
            "cash_weight_percent and cash_value_absolute must both be provided "
            "together, or both omitted."
        )

    total_weight = sum(holding.weight_percent for holding in holdings) + (
        cash_weight_percent or 0.0
    )
    if total_weight > 100 + _ALLOCATION_TOLERANCE:
        raise AlphaPortfolioValidationError(f"Total allocation ({total_weight}%) exceeds 100%.")


def _recompute_weights_from_absolute_values(
    holdings: tuple[AlphaHolding, ...], cash_value: float | None
) -> tuple[tuple[AlphaHolding, ...], float]:
    """Recompute every weight_percent from real absolute values by
    reusing `atlas.domains.portfolio.calculations.holding_weight` -- the
    same calculation engine `projection.py` already reuses -- rather
    than re-deriving the ratio math here (Alpha Sprint 1B: "No
    duplicated calculations. Reuse the existing implementation.")."""
    shared_holdings = tuple(
        SharedHolding(company_id=h.ticker, ticker=h.ticker, market_value=h.value_absolute or 0.0)
        for h in holdings
    )
    cash_holding = SharedHolding(
        company_id=_CASH_TICKER,
        ticker=_CASH_TICKER,
        market_value=cash_value or 0.0,
        asset_type="cash",
    )
    portfolio = SharedPortfolio(
        id="alpha-portfolio", name="Alpha Portfolio", holdings=shared_holdings + (cash_holding,)
    )

    updated_holdings = tuple(
        replace(holding, weight_percent=round(holding_weight(shared, portfolio) * 100, 6))
        for holding, shared in zip(holdings, shared_holdings)
    )
    new_cash_weight = round(holding_weight(cash_holding, portfolio) * 100, 6)
    return updated_holdings, new_cash_weight


def _apply_trade_absolute_mode(
    state: AlphaPortfolioState, entry: AlphaTradeLogEntry, existing: AlphaHolding | None
) -> AlphaPortfolioState:
    """Mode A: real portfolio value is known -- update holding value,
    cash, and recomputed allocation percentages automatically."""
    sign = 1.0 if entry.transaction_type == TransactionType.BUY else -1.0
    trade_value = entry.quantity * entry.execution_price
    fees = entry.fees or 0.0

    if existing is not None:
        new_value = max(0.0, (existing.value_absolute or 0.0) + sign * trade_value)
        updated_holding = replace(
            existing, value_absolute=new_value, reconciliation_status=ReconciliationStatus.UPDATED
        )
        all_holdings = tuple(
            updated_holding if h.ticker == entry.security else h for h in state.holdings
        )
    else:
        new_holding = AlphaHolding(
            ticker=entry.security,
            weight_percent=0.0,
            value_absolute=trade_value,
            reconciliation_status=ReconciliationStatus.UPDATED,
        )
        all_holdings = state.holdings + (new_holding,)

    new_cash_value = max(0.0, (state.cash_value_absolute or 0.0) - sign * trade_value - fees)
    recomputed_holdings, recomputed_cash_weight = _recompute_weights_from_absolute_values(
        all_holdings, new_cash_value
    )

    return replace(
        state,
        holdings=recomputed_holdings,
        cash_value_absolute=new_cash_value,
        cash_weight_percent=recomputed_cash_weight,
        updated_at=_utc_now(),
    )


def _apply_trade_percentage_mode(
    state: AlphaPortfolioState, entry: AlphaTradeLogEntry, existing: AlphaHolding | None
) -> AlphaPortfolioState:
    """Mode B: only percentages are known -- record the trade and flag
    the holding as awaiting reconciliation. Atlas does not invent an
    allocation percentage for it."""
    if existing is not None:
        updated_holding = replace(
            existing, reconciliation_status=ReconciliationStatus.AWAITING_RECONCILIATION
        )
        new_holdings = tuple(
            updated_holding if h.ticker == entry.security else h for h in state.holdings
        )
    else:
        new_holding = AlphaHolding(
            ticker=entry.security,
            weight_percent=0.0,
            reconciliation_status=ReconciliationStatus.AWAITING_RECONCILIATION,
        )
        new_holdings = state.holdings + (new_holding,)

    return replace(state, holdings=new_holdings, updated_at=_utc_now())


class AlphaPortfolioService:
    def __init__(
        self,
        store: AlphaPortfolioStore,
        trade_log_store: AlphaTradeLogStore | None = None,
        outcome_repository: OutcomeRepository | None = None,
    ) -> None:
        self._store = store
        self._trade_log_store = trade_log_store
        self._outcome_repository = outcome_repository

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

        _validate_holdings_and_cash(
            holdings, request.cash_weight_percent, request.cash_value_absolute
        )

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

    def list_trade_log(self) -> list[AlphaTradeLogEntry]:
        if self._trade_log_store is None:
            return []
        return self._trade_log_store.list_all()

    def link_case_to_holding(self, ticker: str, candidate_case_id: str) -> str:
        """Return the authoritative Investment Case id for `ticker`.

        Idempotent get-or-set: if this holding already has a Case linked,
        `candidate_case_id` is ignored and the existing id is returned
        unchanged -- a repeated "Open Investment Case" click must reuse
        the same Case, never create a second one (Alpha Sprint 1A
        Foundation Patch, Defect 1). Only if no Case is linked yet is
        `candidate_case_id` persisted and returned. This holds the
        holding-to-Case association entirely inside this provisional
        Alpha state; no field is added to Core's own Case object for it.
        """
        state = self._store.get()
        if state is None:
            raise AlphaPortfolioNotEstablishedError(
                "No Alpha portfolio has been established yet."
            )

        normalized_ticker = ticker.strip().upper()
        matching = [holding for holding in state.holdings if holding.ticker == normalized_ticker]
        if not matching:
            raise AlphaHoldingNotFoundError(
                f"No holding found for ticker {normalized_ticker!r}."
            )
        holding = matching[0]

        if holding.case_id is not None:
            return holding.case_id

        updated_holding = replace(holding, case_id=candidate_case_id)
        new_holdings = tuple(
            updated_holding if h.ticker == normalized_ticker else h for h in state.holdings
        )
        new_state = replace(state, holdings=new_holdings, updated_at=_utc_now())
        self._store.replace(new_state)
        return candidate_case_id

    def apply_confirmed_trade(self, request: ApplyTradeRequest) -> AlphaPortfolioState:
        """Record a confirmed external trade and update the provisional
        portfolio (Alpha Sprint 1B).

        1. Verify the referenced Outcome exists (read-only Core access).
        2. Verify that Outcome belongs to the given Decision.
        3. Write the `AlphaTradeLogEntry`.
        4. Update the Alpha portfolio -- Mode A (absolute values known)
           recalculates automatically; Mode B (percentages only) records
           the trade and marks the holding as awaiting reconciliation.

        No Core object is read for writing, modified, or originated:
        `self._outcome_repository.get(...)` is the only Core call this
        method makes.
        """
        if self._outcome_repository is None or self._trade_log_store is None:
            raise AlphaPortfolioError(
                "Trade application is not configured for this service instance."
            )

        state = self._store.get()
        if state is None:
            raise AlphaPortfolioNotEstablishedError(
                "No Alpha portfolio has been established yet."
            )

        try:
            outcome_uuid = uuid.UUID(request.outcome_id)
        except ValueError as exc:
            raise AlphaPortfolioValidationError(
                f"outcome_id {request.outcome_id!r} is not a valid id."
            ) from exc

        outcome = self._outcome_repository.get(OutcomeId(outcome_uuid))
        if outcome is None:
            raise OutcomeNotFoundForTradeError(
                f"No Outcome found with id {request.outcome_id!r}."
            )
        if str(outcome.decision_id) != request.decision_id:
            raise DecisionMismatchError(
                f"Outcome {request.outcome_id!r} does not belong to "
                f"Decision {request.decision_id!r}."
            )
        if self._trade_log_store.get_by_outcome_id(request.outcome_id) is not None:
            raise TradeAlreadyAppliedError(
                f"A trade has already been recorded for Outcome {request.outcome_id!r}."
            )

        try:
            trade_entry = AlphaTradeLogEntry(
                outcome_id=request.outcome_id,
                decision_id=request.decision_id,
                security=request.security,
                transaction_type=request.transaction_type,
                quantity=request.quantity,
                execution_price=request.execution_price,
                executed_at=request.executed_at,
                fees=request.fees,
            )
        except ValueError as exc:
            raise AlphaPortfolioValidationError(str(exc)) from exc

        existing = next(
            (holding for holding in state.holdings if holding.ticker == trade_entry.security),
            None,
        )
        if trade_entry.transaction_type == TransactionType.SELL and existing is None:
            raise AlphaPortfolioValidationError(
                f"Cannot record a SELL for {trade_entry.security}: no existing holding found."
            )

        # Absolute-value mode only: reject a trade that is inconsistent
        # with the real dollar figures already known. Without this, a
        # BUY costing more than available cash (or a SELL realizing more
        # than the position's own current value) previously floored the
        # deficit side at zero and let the other side absorb the full
        # trade amount regardless -- silently fabricating portfolio
        # value rather than reporting the inconsistency. Percentage-only
        # mode has no real dollar figures to validate against, so no
        # equivalent check applies there.
        if state.has_absolute_values:
            trade_value = trade_entry.quantity * trade_entry.execution_price
            fees = trade_entry.fees or 0.0
            if trade_entry.transaction_type == TransactionType.BUY:
                available_cash = state.cash_value_absolute or 0.0
                if trade_value + fees > available_cash + _ALLOCATION_TOLERANCE:
                    raise AlphaPortfolioValidationError(
                        f"Cannot record this BUY: cost ({trade_value + fees}) exceeds "
                        f"available cash ({available_cash})."
                    )
            else:
                current_value = (existing.value_absolute if existing else 0.0) or 0.0
                if trade_value > current_value + _ALLOCATION_TOLERANCE:
                    raise AlphaPortfolioValidationError(
                        f"Cannot record this SELL: proceeds ({trade_value}) exceed the "
                        f"holding's current value ({current_value})."
                    )

        self._trade_log_store.add(trade_entry)

        if state.has_absolute_values:
            new_state = _apply_trade_absolute_mode(state, trade_entry, existing)
        else:
            new_state = _apply_trade_percentage_mode(state, trade_entry, existing)

        self._store.replace(new_state)
        return new_state

    def reconcile_update_holding(self, request: UpdateHoldingWeightRequest) -> AlphaPortfolioState:
        """Reconciliation operation 1: update one holding's allocation."""
        state = self._store.get()
        if state is None:
            raise AlphaPortfolioNotEstablishedError(
                "No Alpha portfolio has been established yet."
            )
        if request.weight_percent < 0:
            raise AlphaPortfolioValidationError("weight_percent must not be negative")
        if request.weight_percent > 100:
            raise AlphaPortfolioValidationError("weight_percent must not exceed 100")

        normalized_ticker = request.ticker.strip().upper()
        matching = [holding for holding in state.holdings if holding.ticker == normalized_ticker]
        if not matching:
            raise AlphaHoldingNotFoundError(
                f"No holding found for ticker {normalized_ticker!r}."
            )
        holding = matching[0]

        other_total = sum(
            h.weight_percent for h in state.holdings if h.ticker != normalized_ticker
        ) + (state.cash_weight_percent or 0.0)
        if other_total + request.weight_percent > 100 + _ALLOCATION_TOLERANCE:
            raise AlphaPortfolioValidationError(
                "Updating this holding alone would push total allocation above 100%; "
                "use 'replace entire allocation' instead."
            )

        updated_holding = replace(
            holding,
            weight_percent=request.weight_percent,
            reconciliation_status=ReconciliationStatus.NONE,
        )
        new_holdings = tuple(
            updated_holding if h.ticker == normalized_ticker else h for h in state.holdings
        )
        new_state = replace(state, holdings=new_holdings, updated_at=_utc_now())
        self._store.replace(new_state)
        return new_state

    def reconcile_replace_allocation(
        self, request: ReplaceAllocationRequest
    ) -> AlphaPortfolioState:
        """Reconciliation operation 2: replace the entire allocation.

        Every holding's own Investment Case link (`case_id`) is
        preserved for any ticker that still exists after the replace --
        reconciling allocation must never sever an existing Investment
        Case association.
        """
        state = self._store.get()
        if state is None:
            raise AlphaPortfolioNotEstablishedError(
                "No Alpha portfolio has been established yet."
            )
        if not request.holdings:
            raise AlphaPortfolioValidationError(
                "A replacement allocation must include at least one holding."
            )

        existing_case_ids = {holding.ticker: holding.case_id for holding in state.holdings}
        try:
            holdings = tuple(
                replace(
                    AlphaHolding(
                        ticker=item.ticker,
                        weight_percent=item.weight_percent,
                        value_absolute=item.value_absolute,
                    ),
                    case_id=existing_case_ids.get(item.ticker.strip().upper()),
                )
                for item in request.holdings
            )
        except ValueError as exc:
            raise AlphaPortfolioValidationError(str(exc)) from exc

        _validate_holdings_and_cash(
            holdings, request.cash_weight_percent, request.cash_value_absolute
        )

        new_state = replace(
            state,
            holdings=holdings,
            cash_weight_percent=request.cash_weight_percent,
            cash_value_absolute=request.cash_value_absolute,
            updated_at=_utc_now(),
        )
        self._store.replace(new_state)
        return new_state
