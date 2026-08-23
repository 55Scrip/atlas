"""REST controller for Decision Readiness (Atlas Intelligence Sprint
11). A new top-level prefix, matching `evidence-graph`/`monitoring`'s
own precedent.

`GET /decision-readiness/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id (FastAPI matches in
registration order, the same discipline `evidence_graph.api.router`
already established).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.decision_readiness.api.dependencies import get_decision_readiness_service
from atlas.alpha.decision_readiness.api.schemas import (
    DecisionReadinessChangeView,
    DecisionReadinessComparisonView,
    DecisionReadinessView,
    PortfolioReadinessBreakdownView,
)
from atlas.alpha.decision_readiness.service import DecisionReadinessService

router = APIRouter(prefix="/decision-readiness", tags=["decision-readiness"])


@router.get("/portfolio/breakdown", response_model=PortfolioReadinessBreakdownView)
def get_portfolio_readiness_breakdown(
    service: DecisionReadinessService = Depends(get_decision_readiness_service),
) -> PortfolioReadinessBreakdownView:
    return PortfolioReadinessBreakdownView.from_domain(service.portfolio_breakdown())


@router.get("/compare", response_model=DecisionReadinessComparisonView)
def compare_decision_readiness(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: DecisionReadinessService = Depends(get_decision_readiness_service),
) -> DecisionReadinessComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return DecisionReadinessComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=DecisionReadinessView)
def get_decision_readiness(
    case_id: str, service: DecisionReadinessService = Depends(get_decision_readiness_service)
) -> DecisionReadinessView:
    readiness = service.assess_for_case(case_id)
    if readiness is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return DecisionReadinessView.from_domain(readiness)


@router.get("/{case_id}/change", response_model=DecisionReadinessChangeView | None)
def get_decision_readiness_change(
    case_id: str, service: DecisionReadinessService = Depends(get_decision_readiness_service)
) -> DecisionReadinessChangeView | None:
    change = service.change_for_case(case_id)
    return DecisionReadinessChangeView.from_domain(change) if change is not None else None
