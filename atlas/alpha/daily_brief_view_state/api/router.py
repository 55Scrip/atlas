"""REST controller for Since You Were Here's one piece of new state.

GET  /daily-brief/view-state              - the value BEFORE this visit
POST /daily-brief/view-state/mark-viewed  - set it to now

Deliberately two separate calls, never one combined "read and update"
endpoint: the frontend must read the *previous* `last_viewed_at` to
compute this visit's own "since you were here" window before marking
the new one -- combining them would make that ordering impossible to
express correctly (see this package's own `__init__.py` on why
`last_viewed_at` exists at all).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from atlas.alpha.daily_brief_view_state.api.dependencies import get_daily_brief_view_state_store
from atlas.alpha.daily_brief_view_state.api.schemas import DailyBriefViewStateView
from atlas.alpha.daily_brief_view_state.store import DailyBriefViewStateStore

router = APIRouter(prefix="/daily-brief/view-state", tags=["daily-brief-view-state"])


@router.get("", response_model=DailyBriefViewStateView)
def get_daily_brief_view_state(
    user_id: str = Query(alias="userId"),
    store: DailyBriefViewStateStore = Depends(get_daily_brief_view_state_store),
) -> DailyBriefViewStateView:
    return DailyBriefViewStateView.from_domain(store.get(user_id))


@router.post("/mark-viewed", response_model=DailyBriefViewStateView)
def mark_daily_brief_viewed(
    user_id: str = Query(alias="userId"),
    store: DailyBriefViewStateStore = Depends(get_daily_brief_view_state_store),
) -> DailyBriefViewStateView:
    return DailyBriefViewStateView.from_domain(store.mark_viewed(user_id))
