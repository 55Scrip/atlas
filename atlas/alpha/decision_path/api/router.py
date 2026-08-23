"""REST controller for Decision Path & Required Progress (Atlas
Decision Layer, Sprint 3). A new top-level prefix, matching
`recommendation-conviction`/`investment-decision`'s own precedent.

`GET /decision-path/portfolio/breakdown` and `/compare` are registered
*before* `/{case_id}` below so neither `"portfolio"` nor `"compare"` is
ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.decision_path.api.dependencies import get_decision_path_service
from atlas.alpha.decision_path.api.schemas import (
    DecisionPathChangeView,
    DecisionPathComparisonView,
    DecisionPathView,
    PortfolioDecisionPathBreakdownView,
)
from atlas.alpha.decision_path.service import DecisionPathService

router = APIRouter(prefix="/decision-path", tags=["decision-path"])


@router.get("/portfolio/breakdown", response_model=PortfolioDecisionPathBreakdownView)
def get_portfolio_decision_path_breakdown(
    service: DecisionPathService = Depends(get_decision_path_service),
) -> PortfolioDecisionPathBreakdownView:
    return PortfolioDecisionPathBreakdownView.from_domain(service.portfolio_decision_path_breakdown())


@router.get("/compare", response_model=DecisionPathComparisonView)
def compare_decision_paths(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: DecisionPathService = Depends(get_decision_path_service),
) -> DecisionPathComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return DecisionPathComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=DecisionPathView)
def get_decision_path(case_id: str, service: DecisionPathService = Depends(get_decision_path_service)) -> DecisionPathView:
    path = service.build_for_case(case_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return DecisionPathView.from_domain(path)


@router.get("/{case_id}/change", response_model=DecisionPathChangeView | None)
def get_decision_path_change(
    case_id: str, service: DecisionPathService = Depends(get_decision_path_service)
) -> DecisionPathChangeView | None:
    change = service.change_for_case(case_id)
    return DecisionPathChangeView.from_domain(change) if change is not None else None
