"""REST controller for the Materiality Engine (Atlas Intelligence
Sprint -- Materiality & Priority Engine). A new, sibling top-level
prefix, matching how `stance`/`explainability`/`evidence-quality`/
`evidence-timeline` themselves introduced their own prefix for a
genuinely new report.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.materiality.api.dependencies import get_materiality_service
from atlas.alpha.materiality.api.schemas import MaterialityAssessmentView
from atlas.alpha.materiality.service import MaterialityService

router = APIRouter(prefix="/materiality", tags=["materiality"])


@router.get("/case/{case_id}", response_model=MaterialityAssessmentView)
def get_materiality_for_case(
    case_id: str, service: MaterialityService = Depends(get_materiality_service)
) -> MaterialityAssessmentView:
    assessment = service.assess_for_case(case_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return MaterialityAssessmentView.from_domain(assessment)


@router.get("/ticker/{ticker}", response_model=MaterialityAssessmentView)
def get_materiality_for_ticker(
    ticker: str, service: MaterialityService = Depends(get_materiality_service)
) -> MaterialityAssessmentView:
    assessment = service.assess_for_ticker(ticker)
    if assessment is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for this ticker")
    return MaterialityAssessmentView.from_domain(assessment)
