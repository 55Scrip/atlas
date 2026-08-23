"""REST controller for Decision Memory (Atlas Decision Layer, Sprint
5). A new top-level prefix, matching `opportunity-cost`/`decision-path`'s
own precedent.

`GET /decision-memory/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.decision_memory.api.dependencies import get_decision_memory_service
from atlas.alpha.decision_memory.api.schemas import (
    DecisionMemoryChangeView,
    DecisionMemoryComparisonView,
    DecisionMemoryView,
    PortfolioDecisionMemoryBreakdownView,
)
from atlas.alpha.decision_memory.service import DecisionMemoryService

router = APIRouter(prefix="/decision-memory", tags=["decision-memory"])


@router.get("/portfolio/breakdown", response_model=PortfolioDecisionMemoryBreakdownView)
def get_portfolio_decision_memory_breakdown(
    service: DecisionMemoryService = Depends(get_decision_memory_service),
) -> PortfolioDecisionMemoryBreakdownView:
    return PortfolioDecisionMemoryBreakdownView.from_domain(service.portfolio_decision_memory_breakdown())


@router.get("/compare", response_model=DecisionMemoryComparisonView)
def compare_decision_memory(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: DecisionMemoryService = Depends(get_decision_memory_service),
) -> DecisionMemoryComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return DecisionMemoryComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=DecisionMemoryView)
def get_decision_memory(
    case_id: str, service: DecisionMemoryService = Depends(get_decision_memory_service)
) -> DecisionMemoryView:
    memory = service.assess_for_case(case_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return DecisionMemoryView.from_domain(memory)


@router.get("/{case_id}/change", response_model=DecisionMemoryChangeView | None)
def get_decision_memory_change(
    case_id: str, service: DecisionMemoryService = Depends(get_decision_memory_service)
) -> DecisionMemoryChangeView | None:
    change = service.change_for_case(case_id)
    return DecisionMemoryChangeView.from_domain(change) if change is not None else None
