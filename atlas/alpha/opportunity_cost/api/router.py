"""REST controller for Decision Alternatives & Opportunity Cost (Atlas
Decision Layer, Sprint 4). A new top-level prefix, matching
`decision-path`/`recommendation-conviction`'s own precedent.

`GET /opportunity-cost/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.opportunity_cost.api.dependencies import get_opportunity_cost_service
from atlas.alpha.opportunity_cost.api.schemas import (
    AlternativeComparisonView,
    OpportunityCostChangeView,
    OpportunityCostView,
    PortfolioOpportunityCostBreakdownView,
)
from atlas.alpha.opportunity_cost.service import OpportunityCostService

router = APIRouter(prefix="/opportunity-cost", tags=["opportunity-cost"])


@router.get("/portfolio/breakdown", response_model=PortfolioOpportunityCostBreakdownView)
def get_portfolio_opportunity_cost_breakdown(
    service: OpportunityCostService = Depends(get_opportunity_cost_service),
) -> PortfolioOpportunityCostBreakdownView:
    return PortfolioOpportunityCostBreakdownView.from_domain(service.portfolio_opportunity_cost_breakdown())


@router.get("/compare", response_model=AlternativeComparisonView)
def compare_opportunity_cost(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: OpportunityCostService = Depends(get_opportunity_cost_service),
) -> AlternativeComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return AlternativeComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=OpportunityCostView)
def get_opportunity_cost(
    case_id: str, service: OpportunityCostService = Depends(get_opportunity_cost_service)
) -> OpportunityCostView:
    opportunity_cost = service.assess_for_case(case_id)
    if opportunity_cost is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return OpportunityCostView.from_domain(opportunity_cost)


@router.get("/{case_id}/change", response_model=OpportunityCostChangeView | None)
def get_opportunity_cost_change(
    case_id: str, service: OpportunityCostService = Depends(get_opportunity_cost_service)
) -> OpportunityCostChangeView | None:
    change = service.change_for_case(case_id)
    return OpportunityCostChangeView.from_domain(change) if change is not None else None
