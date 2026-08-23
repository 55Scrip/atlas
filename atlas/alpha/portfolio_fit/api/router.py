"""REST controller for the Portfolio Fit Engine.

A new, sibling top-level prefix (own resource, matching how
`daily_brief`/`portfolio_status`/`portfolio_intelligence` each introduced
their own prefix for a genuinely new report -- see `daily_brief.api
.router`'s own module docstring for the precedent).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.portfolio_fit.api.dependencies import get_portfolio_fit_service
from atlas.alpha.portfolio_fit.api.schemas import FitComparisonView, PortfolioFitAssessmentView
from atlas.alpha.portfolio_fit.service import PortfolioFitService

router = APIRouter(prefix="/portfolio-fit", tags=["portfolio-fit"])


@router.get("/case/{case_id}", response_model=PortfolioFitAssessmentView)
def get_fit_for_case(
    case_id: str, service: PortfolioFitService = Depends(get_portfolio_fit_service)
) -> PortfolioFitAssessmentView:
    """Deliverable 8 -- Investment Case's own "Portfolio Fit" section."""
    assessment = service.assess_for_case(case_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return PortfolioFitAssessmentView.from_domain(assessment)


@router.get("/ticker/{ticker}", response_model=PortfolioFitAssessmentView)
def get_fit_for_ticker(
    ticker: str, service: PortfolioFitService = Depends(get_portfolio_fit_service)
) -> PortfolioFitAssessmentView:
    assessment = service.assess_for_ticker(ticker)
    if assessment is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for this ticker")
    return PortfolioFitAssessmentView.from_domain(assessment)


@router.get("/compare", response_model=FitComparisonView)
def compare_fit(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: PortfolioFitService = Depends(get_portfolio_fit_service),
) -> FitComparisonView:
    """Deliverable 4 -- Company Comparison."""
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for one or both tickers")
    return FitComparisonView.from_domain(comparison)


@router.get("/holdings", response_model=list[PortfolioFitAssessmentView])
def get_fit_for_holdings(
    service: PortfolioFitService = Depends(get_portfolio_fit_service),
) -> list[PortfolioFitAssessmentView]:
    """Deliverable 7 -- Portfolio's own best/worst-fit-today sections."""
    return [PortfolioFitAssessmentView.from_domain(a) for a in service.assess_all_holdings()]


@router.get("/candidates", response_model=list[PortfolioFitAssessmentView])
def get_fit_for_candidates(
    service: PortfolioFitService = Depends(get_portfolio_fit_service),
) -> list[PortfolioFitAssessmentView]:
    """Deliverable 6 -- Discovery's own candidate sort."""
    return [PortfolioFitAssessmentView.from_domain(a) for a in service.rank_candidates()]
