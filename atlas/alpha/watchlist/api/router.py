"""REST controller for Atlas Alpha's provisional Watchlist state
(Investment Case Engine v1 slice).

GET    /alpha-watchlist          - list every Watchlist entry
POST   /alpha-watchlist          - add a ticker (idempotent; links or
                                    reuses its Investment Case and
                                    triggers automatic enrichment)
DELETE /alpha-watchlist/{ticker} - remove a ticker from the Watchlist
                                    only; its Case, Decision history,
                                    and Company data are untouched
                                    (see `service.remove_ticker`)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_service
from atlas.alpha.watchlist.api.schemas import AddWatchlistTickerRequestBody, WatchlistEntryView
from atlas.alpha.watchlist.exceptions import (
    AlphaWatchlistEntryNotFoundError,
    AlphaWatchlistValidationError,
)
from atlas.alpha.watchlist.service import AlphaWatchlistService

router = APIRouter(prefix="/alpha-watchlist", tags=["alpha-watchlist"])


@router.get("", response_model=list[WatchlistEntryView])
def list_watchlist(
    service: AlphaWatchlistService = Depends(get_alpha_watchlist_service),
) -> list[WatchlistEntryView]:
    return [WatchlistEntryView.from_domain(entry) for entry in service.list_all()]


@router.post("", response_model=WatchlistEntryView, status_code=201)
def add_watchlist_ticker(
    payload: AddWatchlistTickerRequestBody,
    service: AlphaWatchlistService = Depends(get_alpha_watchlist_service),
) -> WatchlistEntryView:
    try:
        entry = service.add_ticker(payload.ticker)
    except AlphaWatchlistValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WatchlistEntryView.from_domain(entry)


@router.delete("/{ticker}", status_code=204, response_class=Response)
def remove_watchlist_ticker(
    ticker: str,
    service: AlphaWatchlistService = Depends(get_alpha_watchlist_service),
) -> Response:
    try:
        service.remove_ticker(ticker)
    except AlphaWatchlistEntryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)
