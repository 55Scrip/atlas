"""REST controller for Investment Decision Synthesis (Atlas Decision
Layer, Sprint 1). A new top-level prefix, matching `decision-readiness`/
`evidence-graph`'s own precedent.

`GET /investment-decision/portfolio/distribution` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.investment_decision.api.dependencies import get_investment_decision_service
from atlas.alpha.investment_decision.api.schemas import (
    DecisionChangeView,
    DecisionComparisonView,
    InvestmentDecisionView,
    PortfolioActionDistributionView,
)
from atlas.alpha.investment_decision.service import InvestmentDecisionService

router = APIRouter(prefix="/investment-decision", tags=["investment-decision"])


@router.get("/portfolio/distribution", response_model=PortfolioActionDistributionView)
def get_portfolio_action_distribution(
    service: InvestmentDecisionService = Depends(get_investment_decision_service),
) -> PortfolioActionDistributionView:
    return PortfolioActionDistributionView.from_domain(service.portfolio_action_distribution())


@router.get("/compare", response_model=DecisionComparisonView)
def compare_investment_decisions(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: InvestmentDecisionService = Depends(get_investment_decision_service),
) -> DecisionComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return DecisionComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=InvestmentDecisionView)
def get_investment_decision(
    case_id: str, service: InvestmentDecisionService = Depends(get_investment_decision_service)
) -> InvestmentDecisionView:
    decision = service.synthesize_for_case(case_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return InvestmentDecisionView.from_domain(decision)


@router.get("/{case_id}/change", response_model=DecisionChangeView | None)
def get_investment_decision_change(
    case_id: str, service: InvestmentDecisionService = Depends(get_investment_decision_service)
) -> DecisionChangeView | None:
    change = service.change_for_case(case_id)
    return DecisionChangeView.from_domain(change) if change is not None else None
