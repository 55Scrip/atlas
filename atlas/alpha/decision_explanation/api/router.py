"""REST controller for Decision Explanation (Atlas Decision Layer,
Sprint 6). A new top-level prefix, matching `decision-memory`/
`opportunity-cost`'s own precedent.

`GET /decision-explanation/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.decision_explanation.api.dependencies import get_decision_explanation_service
from atlas.alpha.decision_explanation.api.schemas import (
    DecisionExplanationChangeView,
    DecisionExplanationComparisonView,
    DecisionExplanationView,
    PortfolioDecisionExplanationBreakdownView,
)
from atlas.alpha.decision_explanation.service import DecisionExplanationService

router = APIRouter(prefix="/decision-explanation", tags=["decision-explanation"])


@router.get("/portfolio/breakdown", response_model=PortfolioDecisionExplanationBreakdownView)
def get_portfolio_decision_explanation_breakdown(
    service: DecisionExplanationService = Depends(get_decision_explanation_service),
) -> PortfolioDecisionExplanationBreakdownView:
    return PortfolioDecisionExplanationBreakdownView.from_domain(service.portfolio_decision_explanation_breakdown())


@router.get("/compare", response_model=DecisionExplanationComparisonView)
def compare_decision_explanation(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: DecisionExplanationService = Depends(get_decision_explanation_service),
) -> DecisionExplanationComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return DecisionExplanationComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=DecisionExplanationView)
def get_decision_explanation(
    case_id: str, service: DecisionExplanationService = Depends(get_decision_explanation_service)
) -> DecisionExplanationView:
    explanation = service.build_for_case(case_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return DecisionExplanationView.from_domain(explanation)


@router.get("/{case_id}/change", response_model=DecisionExplanationChangeView | None)
def get_decision_explanation_change(
    case_id: str, service: DecisionExplanationService = Depends(get_decision_explanation_service)
) -> DecisionExplanationChangeView | None:
    change = service.change_for_case(case_id)
    return DecisionExplanationChangeView.from_domain(change) if change is not None else None
