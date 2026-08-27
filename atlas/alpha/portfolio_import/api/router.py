"""REST controller for the unified portfolio import pipeline's preview
step.

POST /alpha-portfolio/import/preview - parse, resolve, and detect
                                        duplicates for raw import text;
                                        never persists anything.

Confirming an import still goes through the existing, unmodified
`POST /alpha-portfolio/import` / `POST /alpha-portfolio/reconcile`
endpoints (`atlas.alpha.portfolio.api.router`).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from atlas.alpha.portfolio_import.api.dependencies import (
    get_existing_tickers,
    get_portfolio_import_preview_service,
)
from atlas.alpha.portfolio_import.api.schemas import ImportPreviewRequestBody, ImportPreviewView
from atlas.alpha.portfolio_import.service import PortfolioImportPreviewService

router = APIRouter(prefix="/alpha-portfolio/import", tags=["alpha-portfolio-import"])


@router.post("/preview", response_model=ImportPreviewView)
def preview_import(
    payload: ImportPreviewRequestBody,
    existing_tickers: frozenset[str] = Depends(get_existing_tickers),
    service: PortfolioImportPreviewService = Depends(get_portfolio_import_preview_service),
) -> ImportPreviewView:
    preview = service.preview(payload.raw_text, existing_tickers)
    return ImportPreviewView.from_domain(preview)
