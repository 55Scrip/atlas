"""REST controller for the Daily Brief Agenda.

A new, sibling top-level prefix (own resource, matching how
`portfolio_fit`/`daily_brief` each introduced their own prefix for a
genuinely new report).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.daily_brief_agenda.api.dependencies import get_daily_brief_agenda_service
from atlas.alpha.daily_brief_agenda.api.schemas import DailyBriefAgendaView
from atlas.alpha.daily_brief_agenda.service import DailyBriefAgendaService

router = APIRouter(prefix="/daily-brief-agenda", tags=["daily-brief-agenda"])


@router.get("", response_model=DailyBriefAgendaView)
def get_daily_brief_agenda(
    service: DailyBriefAgendaService = Depends(get_daily_brief_agenda_service),
) -> DailyBriefAgendaView:
    return DailyBriefAgendaView.from_domain(service.build_agenda())
