"""REST controller for the Investment Case Lifecycle. A new, additive,
read-only endpoint -- does not modify, gate, or wrap any existing
Investment Case endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.investment_case_lifecycle.api.dependencies import get_investment_case_lifecycle_service
from atlas.alpha.investment_case_lifecycle.api.schemas import AtlasStatusView
from atlas.alpha.investment_case_lifecycle.service import InvestmentCaseLifecycleService

router = APIRouter(prefix="/investment-case-lifecycle", tags=["investment-case-lifecycle"])


@router.get("/{case_id}/atlas-status", response_model=AtlasStatusView)
def get_atlas_status(
    case_id: str, service: InvestmentCaseLifecycleService = Depends(get_investment_case_lifecycle_service)
) -> AtlasStatusView:
    status = service.status_for_case(case_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return AtlasStatusView.from_domain(status)
