"""REST controller for the Stance Engine (Atlas Intelligence Sprint 2).

A new, sibling top-level prefix, matching how `portfolio_fit` itself
introduced its own prefix for a genuinely new report (see that
package's own `api/router.py` module docstring for the precedent).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.stance.api.dependencies import get_stance_service
from atlas.alpha.stance.api.schemas import StanceComparisonView, StanceView, TickerStanceView
from atlas.alpha.stance.service import StanceService

router = APIRouter(prefix="/stance", tags=["stance"])


@router.get("/case/{case_id}", response_model=StanceView)
def get_stance_for_case(case_id: str, service: StanceService = Depends(get_stance_service)) -> StanceView:
    stance = service.assess_for_case(case_id)
    if stance is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return StanceView.from_domain(stance)


@router.get("/ticker/{ticker}", response_model=StanceView)
def get_stance_for_ticker(ticker: str, service: StanceService = Depends(get_stance_service)) -> StanceView:
    stance = service.assess_for_ticker(ticker)
    if stance is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for this ticker")
    return StanceView.from_domain(stance)


@router.get("/compare", response_model=StanceComparisonView)
def compare_stance(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: StanceService = Depends(get_stance_service),
) -> StanceComparisonView:
    """Deliverable 9 -- Compare Integration."""
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for one or both tickers")
    return StanceComparisonView.from_domain(comparison)


@router.get("/holdings", response_model=list[TickerStanceView])
def get_stance_for_holdings(service: StanceService = Depends(get_stance_service)) -> list[TickerStanceView]:
    """Deliverable 6 -- Portfolio's own recommendation surface."""
    return [TickerStanceView(ticker=ticker, stance=StanceView.from_domain(stance)) for ticker, stance in service.assess_all_holdings()]


@router.get("/candidates", response_model=list[TickerStanceView])
def get_stance_for_candidates(service: StanceService = Depends(get_stance_service)) -> list[TickerStanceView]:
    """Deliverable 7 -- Discovery's own recommendation-aware cards."""
    return [
        TickerStanceView(ticker=ticker, stance=StanceView.from_domain(stance))
        for ticker, stance in service.assess_for_candidates()
    ]
