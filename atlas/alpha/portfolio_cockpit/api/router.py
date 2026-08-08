"""REST controller for the Portfolio Cockpit (ATLAS-028).

GET /alpha-portfolio/cockpit - read the current Portfolio Cockpit report

A fifth sibling router under the same `/alpha-portfolio` prefix, in its
own module, following the exact `portfolio_status`/`portfolio_intelligence`
/`case_intelligence` precedent -- no new versioning scheme, no change to
any existing route.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.portfolio_cockpit.api.dependencies import get_portfolio_cockpit_service
from atlas.alpha.portfolio_cockpit.api.schemas import PortfolioCockpitView
from atlas.alpha.portfolio_cockpit.service import PortfolioCockpitService

router = APIRouter(prefix="/alpha-portfolio", tags=["alpha-portfolio-cockpit"])


@router.get("/cockpit", response_model=PortfolioCockpitView)
def get_portfolio_cockpit(
    service: PortfolioCockpitService = Depends(get_portfolio_cockpit_service),
) -> PortfolioCockpitView:
    return PortfolioCockpitView.from_domain(service.build_report())
