"""REST controller for Data Ingestion & Automatic Refresh (Atlas
Intelligence Sprint 9). A new, sibling top-level prefix, matching how
`monitoring`/`evidence-timeline` themselves introduced their own
prefix for a genuinely new report.

`POST /ingestion/refresh/{ticker}` is Deliverable 16's own explicit
operation -- always forces a real check against every provider,
regardless of whether the ticker already looks complete (mirrors
`atlas.alpha.monitoring`'s own `force=True` escape hatch). Never
invoked automatically by anything else in this codebase.
`GET /ingestion/results/{case_id}` is a plain read-model lookup, served
from the cache without recomputing.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.case_membership import resolve_case_id_for_ticker
from atlas.alpha.ingestion.api.dependencies import get_ingestion_result_repository, get_ingestion_service
from atlas.alpha.ingestion.api.schemas import IngestionResultView
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.ingestion.service import IngestionService
from atlas.alpha.portfolio.api.dependencies import get_alpha_portfolio_store
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.store import AlphaWatchlistStore

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/refresh/{ticker}", response_model=IngestionResultView)
def refresh_ticker(
    ticker: str,
    service: IngestionService = Depends(get_ingestion_service),
    portfolio_store: AlphaPortfolioStore = Depends(get_alpha_portfolio_store),
    watchlist_store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
) -> IngestionResultView:
    case_id = resolve_case_id_for_ticker(ticker.strip().upper(), portfolio_store, watchlist_store)
    result = service.refresh(ticker.strip().upper(), case_id)
    return IngestionResultView.from_domain(result)


@router.get("/results/{case_id}", response_model=IngestionResultView)
def get_ingestion_result(
    case_id: str, repository: SqlAlchemyIngestionResultRepository = Depends(get_ingestion_result_repository)
) -> IngestionResultView:
    result = repository.get(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No Ingestion result recorded for this Case")
    return IngestionResultView.from_domain(result)
