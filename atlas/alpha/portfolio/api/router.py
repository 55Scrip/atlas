"""REST controller for Atlas Alpha's provisional portfolio state.

GET  /alpha-portfolio                              - read the current derived view
POST /alpha-portfolio/import                        - establish state from an existing portfolio
POST /alpha-portfolio/from-scratch                  - establish state from objective + horizon
POST /alpha-portfolio/holdings/{ticker}/case-link   - get-or-set the Investment Case for a holding
POST /alpha-portfolio/apply-trade                   - record a confirmed external trade (Sprint 1B)
POST /alpha-portfolio/reconcile                     - reconcile allocation after a trade (Sprint 1B)
GET  /alpha-portfolio/trade-log                     - list every recorded trade execution (Sprint 1B)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import (
    ApplyTradeRequestBody,
    CaseLinkResponse,
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

router = APIRouter(prefix="/alpha-portfolio", tags=["alpha-portfolio"])


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
    return PortfolioView.from_domain(state, derive_portfolio_view(state))


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
