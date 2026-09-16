"""REST controller for History v1.

GET /history/analysis - the durable, read-only analytical timeline
across every Case that exists because of Portfolio or Watchlist
membership: what changed, when, and why it mattered, reusing exactly
the persisted `AnalyticalSnapshot`/`ChangeIntelligence` state Investment
Case Change Intelligence already produced. A narrow, dedicated prefix
(`/history`, not a sub-route of `/cases`): the existing History page
already reads three unrelated existing endpoints for investor activity
(Decisions/Outcomes/Observations) client-side, and no History backend
endpoint exists today, so this introduces the smallest new surface
rather than forcing analytical history through one of those unrelated
endpoints or inventing a `/cases/{case_id}/history` per-Case route the
frontend's own unified, cross-Case timeline (Portfolio + Watchlist,
deduplicated, newest first) does not need.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.investment_case_history.api.dependencies import get_investment_case_history_service
from atlas.alpha.investment_case_history.api.schemas import AnalyticalHistoryView
from atlas.alpha.investment_case_history.cursor import InvalidCursorError
from atlas.alpha.investment_case_history.service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    InvestmentCaseHistoryService,
)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/analysis", response_model=AnalyticalHistoryView)
def get_analytical_history(
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE,
                       description="Entries per page; clamped to the maximum."),
    cursor: str | None = Query(None, description="Opaque boundary from a previous page's nextCursor."),
    service: InvestmentCaseHistoryService = Depends(get_investment_case_history_service),
) -> AnalyticalHistoryView:
    """One page of the combined analytical history, newest first.

    Bounded by construction: a request without `limit` receives the default
    page, not the whole corpus. A malformed or superseded `cursor` is a client
    error -- restarting silently at page one would loop a traversal forever.
    """
    try:
        history = service.build_analytical_history(limit=limit, cursor=cursor)
    except InvalidCursorError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return AnalyticalHistoryView.from_domain(history)
