"""REST controller for Case Intelligence (ATLAS-017).

GET /cases/{case_id}/intelligence - read the current Case Intelligence
report for one Investment Case.

404 when the Case itself does not exist, matching `GET /cases/{id}`'s
own existing behavior -- this is a sibling read, not a new resource
identity.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.case_intelligence.api.dependencies import get_case_intelligence_service
from atlas.alpha.case_intelligence.api.schemas import CaseIntelligenceView
from atlas.alpha.case_intelligence.service import CaseIntelligenceService

router = APIRouter(prefix="/cases", tags=["case-intelligence"])


@router.get("/{case_id}/intelligence", response_model=CaseIntelligenceView)
def get_case_intelligence(
    case_id: str,
    service: CaseIntelligenceService = Depends(get_case_intelligence_service),
) -> CaseIntelligenceView:
    report = service.build_report(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseIntelligenceView.from_domain(report)
