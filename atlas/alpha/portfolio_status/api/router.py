"""REST controller for Portfolio Status (ATLAS-015).

GET /alpha-portfolio/status - read the current Portfolio Status report

A second, sibling router to `atlas/alpha/portfolio/api/router.py`'s
under the same `/alpha-portfolio` prefix (FastAPI allows this; the paths
don't collide) -- kept in its own module rather than added to the
existing router so this workflow-completeness concern stays physically
separate from portfolio CRUD/execution, per this sprint's own
"Portfolio Intelligence summarizes, Investment Cases explain..." layering
principle.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.portfolio_status.api.dependencies import get_portfolio_status_service
from atlas.alpha.portfolio_status.api.schemas import PortfolioStatusView
from atlas.alpha.portfolio_status.service import PortfolioStatusService

router = APIRouter(prefix="/alpha-portfolio", tags=["alpha-portfolio-status"])


@router.get("/status", response_model=PortfolioStatusView)
def get_portfolio_status(
    service: PortfolioStatusService = Depends(get_portfolio_status_service),
) -> PortfolioStatusView:
    return PortfolioStatusView.from_domain(service.build_report())
