"""REST controller for Atlas Alpha's provisional portfolio state.

GET  /alpha-portfolio                              - read the current derived view
POST /alpha-portfolio/import                        - establish state from an existing portfolio
POST /alpha-portfolio/from-scratch                  - establish state from objective + horizon
POST /alpha-portfolio/holdings/{ticker}/case-link   - get-or-set the Investment Case for a holding
POST /alpha-portfolio/apply-trade                   - record a confirmed external trade (Sprint 1B)
POST /alpha-portfolio/reconcile                     - reconcile allocation after a trade (Sprint 1B)
GET  /alpha-portfolio/trade-log                     - list every recorded trade execution (Sprint 1B)
POST /alpha-portfolio/enrich                        - bulk-enrich every current holding (Internal Alpha Fix Sprint 1)
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from atlas.alpha.business_data_refresh.api.dependencies import get_default_business_data_providers
from atlas.alpha.business_data_refresh.bulk import enrich_holdings
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import (
    ApplyTradeRequestBody,
    CaseLinkResponse,
    EnrichmentScheduledView,
    FromScratchRequestBody,
    ImportPortfolioRequestBody,
    LinkCaseRequestBody,
    PortfolioView,
    ReconcileRequestBody,
    TradeLogEntryView,
)
from atlas.alpha.portfolio.exceptions import (
    AlphaHoldingNotFoundError,
    AlphaPortfolioNotEstablishedError,
    AlphaPortfolioValidationError,
    DecisionMismatchError,
    OutcomeNotFoundForTradeError,
    TradeAlreadyAppliedError,
)
from atlas.alpha.portfolio.models import TransactionType
from atlas.alpha.portfolio.projection import derive_portfolio_view
from atlas.alpha.portfolio.service import (
    AlphaPortfolioService,
    ApplyTradeRequest,
    FromScratchRequest,
    ImportHoldingInput,
    ImportPortfolioRequest,
    ReplaceAllocationRequest,
    UpdateHoldingWeightRequest,
)
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

router = APIRouter(prefix="/alpha-portfolio", tags=["alpha-portfolio"])


def _run_bulk_enrichment_in_background(tickers: tuple[str, ...]) -> None:
    """Runs on Starlette's background-task thread, after the HTTP
    response has already been sent (Internal Alpha Fix Sprint 1,
    IA-001: "Portfolio import must still complete successfully even if
    enrichment later fails -- they are not the same transaction").

    Deliberately constructs its own fresh `Engine`/repository/providers
    rather than reusing the request-scoped ones FastAPI's `Depends()`
    supplied to the route handler: that `Engine` (from
    `get_decision_engine`, a plain `sqlite:///` connection with no
    `check_same_thread=False`) is bound to the thread that created it --
    the request-handling thread. Reusing it here, on Starlette's
    separate background-task thread, would raise a real sqlite3
    threading error the first time this function actually ran. A freshly
    constructed `Engine`, created on whichever thread calls this
    function, has no such cross-thread history and is safe.
    """
    if not tickers:
        return
    engine = get_decision_engine()
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    providers = get_default_business_data_providers()
    enrich_holdings(tickers, providers, repository)


@router.get("", response_model=PortfolioView)
def get_portfolio(
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> PortfolioView:
    state = service.get_state()
    if state is None:
        return PortfolioView.empty()
    return PortfolioView.from_domain(state, derive_portfolio_view(state))


@router.post("/import", response_model=PortfolioView, status_code=201)
def import_portfolio(
    payload: ImportPortfolioRequestBody,
    background_tasks: BackgroundTasks,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> PortfolioView:
    try:
        state = service.import_portfolio(
            ImportPortfolioRequest(
                holdings=tuple(
                    ImportHoldingInput(
                        ticker=holding.ticker,
                        weight_percent=holding.weight_percent,
                        value_absolute=holding.value_absolute,
                    )
                    for holding in payload.holdings
                ),
                cash_weight_percent=payload.cash_weight_percent,
                cash_value_absolute=payload.cash_value_absolute,
                preferences_notes=payload.preferences_notes,
            )
        )
    except AlphaPortfolioValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    # Internal Alpha Fix Sprint 1, IA-001: import creating Cases with no
    # enrichment was the confirmed root cause. Scheduled *after* the
    # state is already persisted and the response body already built --
    # a provider outage during enrichment can never fail this import.
    background_tasks.add_task(
        _run_bulk_enrichment_in_background, tuple(holding.ticker for holding in state.holdings)
    )
    return PortfolioView.from_domain(state, derive_portfolio_view(state))


@router.post("/enrich", response_model=EnrichmentScheduledView, status_code=202)
def enrich_portfolio(
    background_tasks: BackgroundTasks,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> EnrichmentScheduledView:
    """Internal Alpha Fix Sprint 1, Part 1's explicit backfill path:
    "a clean way to enrich an already imported portfolio... without
    deleting and re-importing it." Every current holding is scheduled
    for the same background enrichment `import_portfolio` now triggers
    automatically -- already-`is_minimally_complete` tickers are
    skipped, unsupported tickers fail honestly, one ticker's failure
    never blocks another's, exactly as `enrich_holdings` guarantees.
    Runs in the background (not the request), so this endpoint
    acknowledges scheduling rather than returning per-ticker outcomes;
    re-opening Portfolio/Investment Case pages afterward is how the
    result becomes visible, the same "import and enrichment are related
    but separate" principle `import_portfolio` itself now follows.
    """
    state = service.get_state()
    if state is None:
        raise HTTPException(status_code=404, detail="No Alpha portfolio has been established yet.")
    tickers = tuple(holding.ticker for holding in state.holdings)
    background_tasks.add_task(_run_bulk_enrichment_in_background, tickers)
    return EnrichmentScheduledView(scheduled_tickers=list(tickers))


@router.post("/from-scratch", response_model=PortfolioView, status_code=201)
def start_from_scratch(
    payload: FromScratchRequestBody,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> PortfolioView:
    try:
        state = service.start_from_scratch(
            FromScratchRequest(
                objective=payload.objective,
                horizon=payload.horizon,
                preferences_notes=payload.preferences_notes,
            )
        )
    except AlphaPortfolioValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PortfolioView.from_domain(state, derive_portfolio_view(state))


@router.post("/holdings/{ticker}/case-link", response_model=CaseLinkResponse)
def link_case_to_holding(
    ticker: str,
    payload: LinkCaseRequestBody,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> CaseLinkResponse:
    try:
        case_id = service.link_case_to_holding(ticker, payload.candidate_case_id)
    except AlphaPortfolioNotEstablishedError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlphaHoldingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CaseLinkResponse(case_id=case_id)


@router.post("/apply-trade", response_model=PortfolioView)
def apply_trade(
    payload: ApplyTradeRequestBody,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> PortfolioView:
    try:
        state = service.apply_confirmed_trade(
            ApplyTradeRequest(
                outcome_id=payload.outcome_id,
                decision_id=payload.decision_id,
                security=payload.security,
                transaction_type=TransactionType(payload.transaction_type),
                quantity=payload.quantity,
                execution_price=payload.execution_price,
                executed_at=payload.executed_at,
                fees=payload.fees,
            )
        )
    except (AlphaPortfolioNotEstablishedError, OutcomeNotFoundForTradeError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TradeAlreadyAppliedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (DecisionMismatchError, AlphaPortfolioValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PortfolioView.from_domain(state, derive_portfolio_view(state))


@router.post("/reconcile", response_model=PortfolioView)
def reconcile(
    payload: ReconcileRequestBody,
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> PortfolioView:
    try:
        if payload.mode == "UPDATE_HOLDING_WEIGHT":
            if payload.ticker is None or payload.weight_percent is None:
                raise AlphaPortfolioValidationError(
                    "ticker and weightPercent are both required for UPDATE_HOLDING_WEIGHT."
                )
            state = service.reconcile_update_holding(
                UpdateHoldingWeightRequest(
                    ticker=payload.ticker, weight_percent=payload.weight_percent
                )
            )
        else:
            if payload.holdings is None:
                raise AlphaPortfolioValidationError(
                    "holdings is required for REPLACE_ALLOCATION."
                )
            state = service.reconcile_replace_allocation(
                ReplaceAllocationRequest(
                    holdings=tuple(
                        ImportHoldingInput(
                            ticker=holding.ticker,
                            weight_percent=holding.weight_percent,
                            value_absolute=holding.value_absolute,
                        )
                        for holding in payload.holdings
                    ),
                    cash_weight_percent=payload.cash_weight_percent,
                    cash_value_absolute=payload.cash_value_absolute,
                )
            )
    except AlphaPortfolioNotEstablishedError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlphaHoldingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlphaPortfolioValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PortfolioView.from_domain(state, derive_portfolio_view(state))


@router.get("/trade-log", response_model=list[TradeLogEntryView])
def list_trade_log(
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> list[TradeLogEntryView]:
    return [TradeLogEntryView.from_domain(entry) for entry in service.list_trade_log()]
