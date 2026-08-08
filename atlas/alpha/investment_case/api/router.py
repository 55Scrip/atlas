"""REST controller for the canonical Investment Case (ATLAS-029).

GET /cases/{case_id}/analysis - read the canonical Investment Case
analysis for one Case, powered by `InvestmentCaseCompositionService`
(ATLAS-027) rather than the older `case_intelligence` path.

A sibling route under the same `/cases` prefix `case_intelligence`'s own
`GET /cases/{case_id}/intelligence` already uses -- additive only. That
older endpoint is left running unmodified this sprint (still consumed by
`discovery_context`); this is the new source `InvestmentCasePage.tsx`
migrates to. 404 on a Case that does not exist, matching
`GET /cases/{case_id}` and `.../intelligence`'s own existing behavior.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.api.schemas import InvestmentCaseAnalysisView
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService

router = APIRouter(prefix="/cases", tags=["investment-case"])


@router.get("/{case_id}/analysis", response_model=InvestmentCaseAnalysisView)
def get_investment_case_analysis(
    case_id: str,
    service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
) -> InvestmentCaseAnalysisView:
    composition = service.build(case_id)
    if composition is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return InvestmentCaseAnalysisView.from_domain(composition)
