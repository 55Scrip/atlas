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

Investment Case Engine v1 slice: `watchlist_store`
(cross-context Case reuse, so a ticker already linked to a Case via
Watchlist is reused rather than duplicated when the same ticker is
added to Portfolio -- see `_ensure_cases`) and
`business_record_repository`/`business_data_providers` (automatic
enrichment for a brand-new holding, see `_trigger_enrichment`) are new,
optional constructor parameters, following the exact `X | None = None`
opt-in pattern `case_generation_service` already established -- every
existing call site that omits them keeps its prior behavior unchanged.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import ensure_company_enriched
from atlas.alpha.canonical_security_gate.gate import CanonicalSecurityIdentityGate
from atlas.alpha.ingestion.engine import classify_refresh
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.case_generation.service import CaseGenerationService
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
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
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
    """`weight_percent` is optional as of Zero-Effort Portfolio Onboarding:
    whenever `value_absolute`, or `quantity` and `price`, are supplied for
    every holding in the batch, weight is always derived from those real
    values rather than trusted from a typed percentage -- see
    `_build_holdings_from_input`. It remains required only in the
    manual-entry fallback, where no value data exists to derive from."""

    ticker: str
    weight_percent: float | None = None
    value_absolute: float | None = None
    quantity: float | None = None
    price: float | None = None
    currency: str | None = None


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


def _resolve_holding_value(item: ImportHoldingInput) -> float | None:
    """The value a holding line resolves to, in priority order: a
    directly-reported value, else quantity x price, else unresolvable
    from this line alone (Zero-Effort Portfolio Onboarding derivation
    algorithm)."""
    if item.value_absolute is not None:
        return item.value_absolute
    if item.quantity is not None and item.price is not None:
        return item.quantity * item.price
    return None


def _build_holdings_from_input(
    items: tuple[ImportHoldingInput, ...],
    cash_value_absolute: float | None,
    existing_case_ids: dict[str, str],
) -> tuple[tuple[AlphaHolding, ...], float | None]:
    """Build final holdings from bulk import input, sharing one derivation
    path between `import_portfolio` and `reconcile_replace_allocation`
    (Zero-Effort Portfolio Onboarding: "weight is always derived").

    A submission must be either fully value-bearing (every holding has a
    value, or quantity and price) -- in which case every weight is
    (re)computed from those real values, discarding any weight_percent
    that happened to also be supplied -- or fully weight-only, the
    manual-entry fallback where no value data exists. Mixing the two
    within one batch has no well-defined total to derive against, so it
    is rejected outright. Returns the built holdings and, when value-
    derivation ran and cash was reported, the derived cash weight
    (`None` otherwise, leaving the caller's own `cash_weight_percent`
    untouched).
    """
    has_value = tuple(_resolve_holding_value(item) is not None for item in items)
    all_value_bearing = all(has_value)
    none_value_bearing = not any(has_value)

    if not all_value_bearing and not none_value_bearing:
        raise AlphaPortfolioValidationError(
            "Provide either a value (or quantity and price) for every holding, "
            "or a weight percentage for every holding -- not a mix of the two."
        )

    if none_value_bearing:
        for item in items:
            if item.weight_percent is None:
                raise AlphaPortfolioValidationError(
                    f"Holding {item.ticker!r} has neither a weight percentage nor "
                    "enough data (a value, or quantity and price) to determine its size."
                )
        holdings = tuple(
            replace(
                AlphaHolding(
                    ticker=item.ticker,
                    weight_percent=item.weight_percent,
                    value_absolute=item.value_absolute,
                    quantity=item.quantity,
                    price=item.price,
                    currency=item.currency,
                ),
                case_id=existing_case_ids.get(item.ticker.strip().upper()),
            )
            for item in items
        )
        return holdings, None

    currencies = {
        item.currency.strip().upper() for item in items if item.currency and item.currency.strip()
    }
    if len(currencies) > 1:
        raise AlphaPortfolioValidationError(
            f"Holdings report more than one currency ({', '.join(sorted(currencies))}); "
            "cannot derive portfolio weights across mixed currencies."
        )

    interim_holdings = tuple(
        replace(
            AlphaHolding(
                ticker=item.ticker,
                weight_percent=0.0,
                value_absolute=_resolve_holding_value(item),
                quantity=item.quantity,
                price=item.price,
                currency=item.currency,
            ),
            case_id=existing_case_ids.get(item.ticker.strip().upper()),
        )
        for item in items
    )
    recomputed_holdings, recomputed_cash_weight = _recompute_weights_from_absolute_values(
        interim_holdings, cash_value_absolute
    )
    derived_cash_weight = recomputed_cash_weight if cash_value_absolute is not None else None
    return recomputed_holdings, derived_cash_weight


def _apply_trade_absolute_mode(
    state: AlphaPortfolioState, entry: AlphaTradeLogEntry, existing: AlphaHolding | None
) -> AlphaPortfolioState:
    """Mode A: real portfolio value is known -- update holding value,
    cash, and recomputed allocation percentages automatically. Only
    ever called for BUY/ADD/SELL -- EXIT has its own dedicated path
    (`_apply_trade_exit_mode`) since closing a position removes the
    holding rather than adjusting its value."""
    sign = 1.0 if entry.transaction_type in (TransactionType.BUY, TransactionType.ADD) else -1.0
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


def _apply_trade_exit_mode(
    state: AlphaPortfolioState, entry: AlphaTradeLogEntry
) -> AlphaPortfolioState:
    """EXIT (ATLAS-014): the position is fully closed -- remove the
    holding outright rather than reduce it, in both modes. The
    holding's Investment Case link goes with it (there is no more
    holding to hold the association), but the Investment Case itself,
    and every Decision and Outcome ever recorded against it, live
    entirely in Core and are untouched by this.

    Mode A additionally credits the sale proceeds to cash and
    recomputes the remaining holdings' weights from real values, reusing
    the same calculation engine `_apply_trade_absolute_mode` does. Mode
    B leaves every remaining holding's percentage exactly as it was --
    the portfolio's total will no longer sum to 100%, which is the same
    honest "incomplete allocation" state Portfolio Import already
    discloses, not a gap Atlas invents a number to fill.
    """
    remaining_holdings = tuple(h for h in state.holdings if h.ticker != entry.security)

    if not state.has_absolute_values:
        return replace(state, holdings=remaining_holdings, updated_at=_utc_now())

    trade_value = entry.quantity * entry.execution_price
    fees = entry.fees or 0.0
    new_cash_value = max(0.0, (state.cash_value_absolute or 0.0) + trade_value - fees)
    recomputed_holdings, recomputed_cash_weight = _recompute_weights_from_absolute_values(
        remaining_holdings, new_cash_value
    )
    return replace(
        state,
        holdings=recomputed_holdings,
        cash_value_absolute=new_cash_value,
        cash_weight_percent=recomputed_cash_weight,
        updated_at=_utc_now(),
    )


class AlphaPortfolioService:
    def __init__(
        self,
        store: AlphaPortfolioStore,
        trade_log_store: AlphaTradeLogStore | None = None,
        outcome_repository: OutcomeRepository | None = None,
        case_generation_service: CaseGenerationService | None = None,
        watchlist_store: AlphaWatchlistStore | None = None,
        business_record_repository: SqlAlchemyBusinessRecordRepository | None = None,
        business_data_providers: tuple[BusinessDataProvider, ...] | None = None,
        identity_gate: CanonicalSecurityIdentityGate | None = None,
        ingestion_result_repository: SqlAlchemyIngestionResultRepository | None = None,
    ) -> None:
        self._store = store
        self._trade_log_store = trade_log_store
        self._outcome_repository = outcome_repository
        self._case_generation_service = case_generation_service
        self._watchlist_store = watchlist_store
        self._business_record_repository = business_record_repository
        self._business_data_providers = business_data_providers
        self._identity_gate = identity_gate
        self._ingestion_result_repository = ingestion_result_repository

    def _known_watchlist_case_ids(self) -> dict[str, str]:
        """(Investment Case Engine v1 slice) Watchlist's own entries,
        ticker -> case_id -- so a ticker already linked to a Case via
        Watchlist is reused, never duplicated, when the same ticker is
        added to Portfolio. Mirrors `case_membership
        .resolve_case_id_for_ticker`'s identical cross-context lookup
        in the other direction.

        Ticker -> Existing Case Resolution Sprint: deliberately
        includes removed Watchlist entries too
        (`list_all_including_removed`), not just current ones -- a
        ticker imported into Portfolio for the first time after being
        removed from the Watchlist (never re-added) must still reuse
        its original Case rather than getting a second one, the exact
        same continuity guarantee `resolve_case_id_for_ticker` gives
        Watchlist's own re-add path."""
        if self._watchlist_store is None:
            return {}
        return {entry.ticker: entry.case_id for entry in self._watchlist_store.list_all_including_removed()}

    def _ensure_cases(self, holdings: tuple[AlphaHolding, ...]) -> tuple[AlphaHolding, ...]:
        """ATLAS-027: every real composition root wires
        `case_generation_service`; `None` is accepted only so callers
        that intentionally test unrelated behavior (or don't care about
        automatic Case existence) may construct this service without it
        -- in that case every holding is returned exactly as given,
        `case_id` untouched, the same behavior this method's callers had
        before ATLAS-027 existed."""
        if self._case_generation_service is None:
            return holdings
        return self._case_generation_service.ensure_cases(
            holdings, known_case_ids_by_ticker=self._known_watchlist_case_ids()
        )

    def _trigger_enrichment(self, ticker: str, case_id: str | None = None) -> None:
        """(Investment Case Engine v1 slice) Best-effort, never raises:
        see `AlphaWatchlistService._trigger_enrichment`'s identical
        docstring for the full rationale -- this is the same no-op-if-
        undependency-absent, idempotent-if-already-enriched trigger,
        reused here rather than redefined. Sprint O: `identity_gate`
        joins the other two as a third all-or-nothing dependency.
        Atlas Intelligence Sprint 9: records the resulting
        `RefreshSummary` as this Case's own `IngestionResult`, same
        rationale as `AlphaWatchlistService`'s own identical addition."""
        if (
            self._business_record_repository is None
            or self._business_data_providers is None
            or self._identity_gate is None
        ):
            return
        # Automatic Enrichment Coverage, Implementation Phase 1: the
        # prior run's own classified failures (if any), so a provider
        # already known `FAILED_UNSUPPORTED` for this ticker is not
        # retried -- see `AlphaWatchlistService._trigger_enrichment`'s
        # identical comment for the full rationale.
        known_provider_failures: tuple = ()
        if self._ingestion_result_repository is not None:
            prior = self._ingestion_result_repository.get_by_ticker(ticker)
            if prior is not None:
                known_provider_failures = prior.provider_failures
        summary = ensure_company_enriched(
            ticker, self._business_data_providers, self._business_record_repository,
            identity_gate=self._identity_gate,
            known_provider_failures=known_provider_failures,
        )
        if summary is not None and self._ingestion_result_repository is not None:
            result = classify_refresh(summary, ticker=ticker, case_id=case_id, ran_at=summary.evaluated_at or _utc_now())
            self._ingestion_result_repository.upsert(result)

    def import_portfolio(self, request: ImportPortfolioRequest) -> AlphaPortfolioState:
        """Establish (or re-establish) the Alpha portfolio from an
        existing-portfolio import.

        ATLAS-027: any `case_id` already linked to a ticker in the
        *current* state is carried forward into the freshly-built
        holdings for that same ticker -- mirroring
        `reconcile_replace_allocation`'s own pre-existing
        `existing_case_ids` pattern exactly. Before this fix, import
        always started every holding at `case_id=None`, silently
        severing every existing Investment Case link on every
        re-import; that was a real bug, not intended behavior (Phase 5's
        own "re-import same portfolio -> no new Case" requirement). Every
        holding that still lacks a `case_id` after that carry-forward
        -- including every holding on a genuinely first import -- gets
        one via `_ensure_cases`.
        """
        if not request.holdings:
            raise AlphaPortfolioValidationError(
                "An imported portfolio must include at least one holding."
            )
        previous_state = self._store.get()
        existing_case_ids = (
            {holding.ticker: holding.case_id for holding in previous_state.holdings}
            if previous_state is not None
            else {}
        )
        try:
            holdings, derived_cash_weight_percent = _build_holdings_from_input(
                request.holdings, request.cash_value_absolute, existing_case_ids
            )
        except ValueError as exc:
            raise AlphaPortfolioValidationError(str(exc)) from exc

        cash_weight_percent = (
            derived_cash_weight_percent
            if derived_cash_weight_percent is not None
            else request.cash_weight_percent
        )
        _validate_holdings_and_cash(holdings, cash_weight_percent, request.cash_value_absolute)
        holdings = self._ensure_cases(holdings)

        now = _utc_now()
        state = AlphaPortfolioState(
            established_at=now,
            updated_at=now,
            entry_mode=EntryMode.IMPORTED,
            holdings=holdings,
            cash_weight_percent=cash_weight_percent,
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
        portfolio (Alpha Sprint 1B; EXIT added by ATLAS-014).

        1. Verify the referenced Outcome exists (read-only Core access).
        2. Verify that Outcome belongs to the given Decision.
        3. Write the `AlphaTradeLogEntry` -- this is the durable,
           append-only record of the execution (`GET /alpha-portfolio
           /trade-log`); a future History page reads from here.
        4. Update the Alpha portfolio: EXIT removes the holding outright
           in both modes (`_apply_trade_exit_mode`); BUY/ADD/SELL update
           it via Mode A (absolute values known -- recalculates
           automatically) or Mode B (percentages only -- records the
           trade and marks the holding as awaiting reconciliation).

        No Core object is read for writing, modified, or originated:
        `self._outcome_repository.get(...)` is the only Core call this
        method makes. The Decision and Outcome this trade follows from
        are never touched -- only referenced by id.
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
        if (
            trade_entry.transaction_type in (TransactionType.SELL, TransactionType.EXIT)
            and existing is None
        ):
            raise AlphaPortfolioValidationError(
                f"Cannot record a {trade_entry.transaction_type.value} for "
                f"{trade_entry.security}: no existing holding found."
            )

        # Absolute-value mode only: reject a trade that is inconsistent
        # with the real dollar figures already known. Without this, a
        # BUY costing more than available cash (or a SELL/EXIT realizing
        # more than the position's own current value) previously
        # floored the deficit side at zero and let the other side
        # absorb the full trade amount regardless -- silently
        # fabricating portfolio value rather than reporting the
        # inconsistency. Percentage-only mode has no real dollar
        # figures to validate against, so no equivalent check applies
        # there.
        if state.has_absolute_values:
            trade_value = trade_entry.quantity * trade_entry.execution_price
            fees = trade_entry.fees or 0.0
            if trade_entry.transaction_type in (TransactionType.BUY, TransactionType.ADD):
                available_cash = state.cash_value_absolute or 0.0
                if trade_value + fees > available_cash + _ALLOCATION_TOLERANCE:
                    raise AlphaPortfolioValidationError(
                        f"Cannot record this {trade_entry.transaction_type.value}: cost "
                        f"({trade_value + fees}) exceeds available cash ({available_cash})."
                    )
            else:
                current_value = (existing.value_absolute if existing else 0.0) or 0.0
                if trade_value > current_value + _ALLOCATION_TOLERANCE:
                    raise AlphaPortfolioValidationError(
                        f"Cannot record this {trade_entry.transaction_type.value}: proceeds "
                        f"({trade_value}) exceed the holding's current value ({current_value})."
                    )

        self._trade_log_store.add(trade_entry)

        if trade_entry.transaction_type == TransactionType.EXIT:
            new_state = _apply_trade_exit_mode(state, trade_entry)
        elif state.has_absolute_values:
            new_state = _apply_trade_absolute_mode(state, trade_entry, existing)
        else:
            new_state = _apply_trade_percentage_mode(state, trade_entry, existing)

        # ATLAS-027 Phase 5: a BUY/ADD on a ticker not previously held
        # creates a brand-new `AlphaHolding` with `case_id=None` (see
        # `_apply_trade_absolute_mode`/`_apply_trade_percentage_mode`'s
        # own "else" branches) -- "new holding added -> one new Case."
        # EXIT only ever removes holdings, so this is always a no-op for
        # that branch; harmless and correct to apply uniformly.
        new_state = replace(new_state, holdings=self._ensure_cases(new_state.holdings))

        # Investment Case Engine v1 slice: automatic enrichment fires
        # only for a genuinely new position (`existing is None`, i.e. a
        # ticker not previously held) being opened (`BUY`/`ADD`) -- the
        # realistic single-company "add to Portfolio" moment. Adding to
        # an already-held position, a `SELL`, or an `EXIT` never
        # triggers a fetch: the ticker either already has persisted
        # `BusinessRecord`s (so `ensure_company_enriched` would no-op
        # anyway) or is being reduced/closed, not newly introduced.
        # Deliberately NOT wired into the bulk `import_portfolio`/
        # `reconcile_replace_allocation` paths -- see the design
        # record's Known Limitations for why a bulk, many-ticker import
        # synchronously triggering many sequential provider calls is
        # out of this slice's scope.
        if existing is None and trade_entry.transaction_type in (TransactionType.BUY, TransactionType.ADD):
            new_case_id = next((h.case_id for h in new_state.holdings if h.ticker == trade_entry.security), None)
            self._trigger_enrichment(trade_entry.security, new_case_id)

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
            holdings, derived_cash_weight_percent = _build_holdings_from_input(
                request.holdings, request.cash_value_absolute, existing_case_ids
            )
        except ValueError as exc:
            raise AlphaPortfolioValidationError(str(exc)) from exc

        cash_weight_percent = (
            derived_cash_weight_percent
            if derived_cash_weight_percent is not None
            else request.cash_weight_percent
        )
        _validate_holdings_and_cash(holdings, cash_weight_percent, request.cash_value_absolute)
        holdings = self._ensure_cases(holdings)

        new_state = replace(
            state,
            holdings=holdings,
            cash_weight_percent=cash_weight_percent,
            cash_value_absolute=request.cash_value_absolute,
            updated_at=_utc_now(),
        )
        self._store.replace(new_state)
        return new_state
