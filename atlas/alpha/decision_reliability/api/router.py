"""REST controller for Decision Reliability (Atlas Decision Layer,
Sprint 7). A new top-level prefix, matching `decision-explanation`/
`decision-memory`'s own precedent.

`GET /decision-reliability/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.decision_reliability.api.dependencies import get_decision_reliability_service
from atlas.alpha.decision_reliability.api.schemas import (
    DecisionReliabilityView,
    PortfolioReliabilityBreakdownView,
    ReliabilityChangeView,
    ReliabilityComparisonView,
)
from atlas.alpha.decision_reliability.service import DecisionReliabilityService

router = APIRouter(prefix="/decision-reliability", tags=["decision-reliability"])


@router.get("/portfolio/breakdown", response_model=PortfolioReliabilityBreakdownView)
def get_portfolio_reliability_breakdown(
    service: DecisionReliabilityService = Depends(get_decision_reliability_service),
) -> PortfolioReliabilityBreakdownView:
    return PortfolioReliabilityBreakdownView.from_domain(service.portfolio_reliability_breakdown())


@router.get("/compare", response_model=ReliabilityComparisonView)
def compare_decision_reliability(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: DecisionReliabilityService = Depends(get_decision_reliability_service),
) -> ReliabilityComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return ReliabilityComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=DecisionReliabilityView)
def get_decision_reliability(
    case_id: str, service: DecisionReliabilityService = Depends(get_decision_reliability_service)
) -> DecisionReliabilityView:
    reliability = service.assess_for_case(case_id)
    if reliability is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return DecisionReliabilityView.from_domain(reliability)


@router.get("/{case_id}/change", response_model=ReliabilityChangeView | None)
def get_decision_reliability_change(
    case_id: str, service: DecisionReliabilityService = Depends(get_decision_reliability_service)
) -> ReliabilityChangeView | None:
    change = service.change_for_case(case_id)
    return ReliabilityChangeView.from_domain(change) if change is not None else None
