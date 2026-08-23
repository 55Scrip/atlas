"""REST controller for Portfolio Decision Synthesis (Atlas Decision
Layer, Sprint 8). A new top-level prefix, matching
`decision-reliability`/`decision-explanation`'s own precedent.

`GET /portfolio-decision/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.portfolio_decision.api.dependencies import get_portfolio_decision_service
from atlas.alpha.portfolio_decision.api.schemas import (
    PortfolioDecisionChangeView,
    PortfolioDecisionComparisonView,
    PortfolioDecisionView,
    PortfolioSynthesisBreakdownView,
)
from atlas.alpha.portfolio_decision.service import PortfolioDecisionService

router = APIRouter(prefix="/portfolio-decision", tags=["portfolio-decision"])


@router.get("/portfolio/breakdown", response_model=PortfolioSynthesisBreakdownView)
def get_portfolio_synthesis_breakdown(
    service: PortfolioDecisionService = Depends(get_portfolio_decision_service),
) -> PortfolioSynthesisBreakdownView:
    return PortfolioSynthesisBreakdownView.from_domain(service.portfolio_synthesis_breakdown())


@router.get("/compare", response_model=PortfolioDecisionComparisonView)
def compare_portfolio_decision(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: PortfolioDecisionService = Depends(get_portfolio_decision_service),
) -> PortfolioDecisionComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return PortfolioDecisionComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=PortfolioDecisionView)
def get_portfolio_decision(
    case_id: str, service: PortfolioDecisionService = Depends(get_portfolio_decision_service)
) -> PortfolioDecisionView:
    decision = service.assess_for_case(case_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return PortfolioDecisionView.from_domain(decision)


@router.get("/{case_id}/change", response_model=PortfolioDecisionChangeView | None)
def get_portfolio_decision_change(
    case_id: str, service: PortfolioDecisionService = Depends(get_portfolio_decision_service)
) -> PortfolioDecisionChangeView | None:
    change = service.change_for_case(case_id)
    return PortfolioDecisionChangeView.from_domain(change) if change is not None else None
