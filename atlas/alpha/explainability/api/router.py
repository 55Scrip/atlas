"""REST controller for the Explainability Engine (Atlas Intelligence
Sprint 3).

A new, sibling top-level prefix, matching how `stance` itself
introduced its own prefix for a genuinely new report.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.explainability.api.dependencies import get_explainability_service
from atlas.alpha.explainability.api.schemas import ComparisonEvidenceView, ExplanationView
from atlas.alpha.explainability.service import ExplainabilityService

router = APIRouter(prefix="/explainability", tags=["explainability"])


@router.get("/case/{case_id}", response_model=ExplanationView)
def get_explanation_for_case(
    case_id: str, service: ExplainabilityService = Depends(get_explainability_service)
) -> ExplanationView:
    explanation = service.explain_for_case(case_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return ExplanationView.from_domain(explanation)


@router.get("/ticker/{ticker}", response_model=ExplanationView)
def get_explanation_for_ticker(
    ticker: str, service: ExplainabilityService = Depends(get_explainability_service)
) -> ExplanationView:
    explanation = service.explain_for_ticker(ticker)
    if explanation is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for this ticker")
    return ExplanationView.from_domain(explanation)


@router.get("/compare", response_model=ComparisonEvidenceView)
def compare_explanations(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: ExplainabilityService = Depends(get_explainability_service),
) -> ComparisonEvidenceView:
    """Deliverable 7 -- Compare Integration."""
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for one or both tickers")
    return ComparisonEvidenceView.from_domain(comparison)
