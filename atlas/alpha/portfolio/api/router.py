"""REST controller for Atlas Alpha's provisional portfolio state.

GET  /alpha-portfolio               - read the current derived view
POST /alpha-portfolio/import        - establish state from an existing portfolio
POST /alpha-portfolio/from-scratch  - establish state from objective + horizon

Sprint 1A scope only: no trade-application or reconciliation endpoint
exists yet (Sprint 1B).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_service
from atlas.alpha.portfolio.api.schemas import (
    FromScratchRequestBody,
    ImportPortfolioRequestBody,
    PortfolioView,
)
from atlas.alpha.portfolio.exceptions import AlphaPortfolioValidationError
from atlas.alpha.portfolio.service import (
    AlphaPortfolioService,
    FromScratchRequest,
    ImportHoldingInput,
    ImportPortfolioRequest,
)

router = APIRouter(prefix="/alpha-portfolio", tags=["alpha-portfolio"])


@router.get("", response_model=PortfolioView)
def get_portfolio(
    service: AlphaPortfolioService = Depends(get_alpha_portfolio_service),
) -> PortfolioView:
    state = service.get_state()
    if state is None:
        return PortfolioView.empty()
    view = service.get_view()
    assert view is not None
    return PortfolioView.from_domain(state, view)


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
    view = service.get_view()
    assert view is not None
    return PortfolioView.from_domain(state, view)


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
    view = service.get_view()
    assert view is not None
    return PortfolioView.from_domain(state, view)
