"""REST controller for Daily Brief v1.

GET /daily-brief - read today's Daily Brief: which companies (Portfolio
holdings or Watchlist entries) have a meaningful Investment Case Change
Intelligence update since their previous analysis, and why it matters.
A new, sibling top-level prefix (own resource, not a sub-route of
`/alpha-portfolio` or `/cases`), matching how `portfolio_status`/
`portfolio_intelligence`/`portfolio_cockpit` each introduced their own
prefix for a genuinely new report.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.daily_brief.api.dependencies import get_daily_brief_service
from atlas.alpha.daily_brief.api.schemas import DailyBriefView
from atlas.alpha.daily_brief.service import DailyBriefService

router = APIRouter(prefix="/daily-brief", tags=["daily-brief"])


@router.get("", response_model=DailyBriefView)
def get_daily_brief(service: DailyBriefService = Depends(get_daily_brief_service)) -> DailyBriefView:
    return DailyBriefView.from_domain(service.build_daily_brief())
