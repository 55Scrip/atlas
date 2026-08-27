"""REST controller for Daily Brief 2.0's change log.

GET  /daily-brief-change-log              - live (non-archived) changes, one group per ticker
POST /daily-brief-change-log/mark-seen    - mark a set of changes seen

Deliberately read/update only here -- the *write* path (recording a
newly-observed eligible change) is a side effect of
`GET /daily-brief-agenda` itself (`daily_brief_agenda/api/router.py`),
not a third endpoint, since a change can only ever be recorded from a
freshly-built agenda and this package must never rebuild that agenda a
second time just to log it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from atlas.alpha.daily_brief_change_log.api.dependencies import get_daily_brief_change_log_store
from atlas.alpha.daily_brief_change_log.api.schemas import MarkSeenRequest, TickerChangeGroupView
from atlas.alpha.daily_brief_change_log.store import DailyBriefChangeLogStore
from atlas.alpha.daily_brief_change_log.synthesis import group_by_ticker

router = APIRouter(prefix="/daily-brief-change-log", tags=["daily-brief-change-log"])


@router.get("", response_model=list[TickerChangeGroupView])
def get_daily_brief_change_log(
    user_id: str = Query(alias="userId"),
    store: DailyBriefChangeLogStore = Depends(get_daily_brief_change_log_store),
) -> list[TickerChangeGroupView]:
    entries = store.list_recent(user_id)
    groups = group_by_ticker(entries)
    return [TickerChangeGroupView.from_domain(group) for group in groups]


@router.post("/mark-seen", response_model=list[TickerChangeGroupView])
def mark_daily_brief_changes_seen(
    request: MarkSeenRequest,
    user_id: str = Query(alias="userId"),
    store: DailyBriefChangeLogStore = Depends(get_daily_brief_change_log_store),
) -> list[TickerChangeGroupView]:
    store.mark_seen(user_id, tuple(request.change_ids))
    entries = store.list_recent(user_id)
    groups = group_by_ticker(entries)
    return [TickerChangeGroupView.from_domain(group) for group in groups]
