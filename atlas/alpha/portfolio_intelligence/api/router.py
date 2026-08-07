"""REST controller for Portfolio Intelligence (ATLAS-016).

GET /alpha-portfolio/intelligence - read the current Portfolio
Intelligence report.

A sibling router to `atlas/alpha/portfolio_status/api/router.py`'s,
under the same `/alpha-portfolio` prefix -- kept in its own module for
the same reason that one is separate from portfolio CRUD/execution:
this is a distinct concern (investment intelligence, consuming the
Decision Engine) from workflow-completeness status (ATLAS-015).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.portfolio_intelligence.api.dependencies import get_portfolio_intelligence_service
from atlas.alpha.portfolio_intelligence.api.schemas import PortfolioIntelligenceView
from atlas.alpha.portfolio_intelligence.service import PortfolioIntelligenceService

router = APIRouter(prefix="/alpha-portfolio", tags=["alpha-portfolio-intelligence"])


@router.get("/intelligence", response_model=PortfolioIntelligenceView)
def get_portfolio_intelligence(
    service: PortfolioIntelligenceService = Depends(get_portfolio_intelligence_service),
) -> PortfolioIntelligenceView:
    return PortfolioIntelligenceView.from_domain(service.build_report())
