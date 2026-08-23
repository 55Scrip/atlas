"""REST controller for Recommendation Conviction & Strength (Atlas
Decision Layer, Sprint 2). A new top-level prefix, matching
`investment-decision`/`decision-readiness`'s own precedent.

`GET /recommendation-conviction/portfolio/breakdown` and `/compare` are
registered *before* `/{case_id}` below so neither `"portfolio"` nor
`"compare"` is ever swallowed as a case id.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.recommendation_conviction.api.dependencies import get_recommendation_conviction_service
from atlas.alpha.recommendation_conviction.api.schemas import (
    ConvictionChangeView,
    ConvictionComparisonView,
    PortfolioConvictionBreakdownView,
    RecommendationConvictionView,
)
from atlas.alpha.recommendation_conviction.service import RecommendationConvictionService

router = APIRouter(prefix="/recommendation-conviction", tags=["recommendation-conviction"])


@router.get("/portfolio/breakdown", response_model=PortfolioConvictionBreakdownView)
def get_portfolio_conviction_breakdown(
    service: RecommendationConvictionService = Depends(get_recommendation_conviction_service),
) -> PortfolioConvictionBreakdownView:
    return PortfolioConvictionBreakdownView.from_domain(service.portfolio_conviction_breakdown())


@router.get("/compare", response_model=ConvictionComparisonView)
def compare_recommendation_conviction(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: RecommendationConvictionService = Depends(get_recommendation_conviction_service),
) -> ConvictionComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return ConvictionComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=RecommendationConvictionView)
def get_recommendation_conviction(
    case_id: str, service: RecommendationConvictionService = Depends(get_recommendation_conviction_service)
) -> RecommendationConvictionView:
    conviction = service.assess_for_case(case_id)
    if conviction is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return RecommendationConvictionView.from_domain(conviction)


@router.get("/{case_id}/change", response_model=ConvictionChangeView | None)
def get_recommendation_conviction_change(
    case_id: str, service: RecommendationConvictionService = Depends(get_recommendation_conviction_service)
) -> ConvictionChangeView | None:
    change = service.change_for_case(case_id)
    return ConvictionChangeView.from_domain(change) if change is not None else None
