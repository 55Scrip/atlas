"""REST controller for Atlas Alpha's provisional Watchlist state
(Investment Case Engine v1 slice).

GET    /alpha-watchlist          - list every Watchlist entry
POST   /alpha-watchlist          - add a ticker (idempotent; links or
                                    reuses its Investment Case, triggers
                                    automatic enrichment, and schedules
                                    an automatic Monitoring run)
DELETE /alpha-watchlist/{ticker} - remove a ticker from the Watchlist
                                    only; its Case, Decision history,
                                    and Company data are untouched
                                    (see `service.remove_ticker`)

**Internal Alpha Fix Sprint 1, Deliverable 5 (Portfolio Change
Integration).** Adding a ticker is exactly the "genuinely new
information" event Deliverable 5 asks to integrate: a brand-new Case has
never been monitored (`needs_recompute` is unconditionally `True` for
it), so it will always be picked up. Scheduled as a `BackgroundTasks`
job, same as `atlas.alpha.portfolio.api.router`'s own bulk-enrichment
scheduling and for the identical reason: the caller already got a
successful response the moment the ticker was added; a Monitoring
hiccup afterward must never turn a successful add into a slow or failed
one.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response

from atlas.alpha.monitoring.api.dependencies import build_monitoring_service
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_service
from atlas.alpha.investment_case.api.dependencies import get_investment_case_composition_service
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.decision_support import describe_recommendation
from atlas.alpha.watchlist.api.dependencies import get_alpha_watchlist_store
from atlas.alpha.watchlist.api.schemas import (
    AddWatchlistTickerRequestBody,
    WatchlistEntrySummaryView,
    WatchlistEntryView,
)
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.exceptions import (
    AlphaWatchlistEntryNotFoundError,
    AlphaWatchlistValidationError,
)
from atlas.alpha.watchlist.service import AlphaWatchlistService
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

router = APIRouter(prefix="/alpha-watchlist", tags=["alpha-watchlist"])


def _trigger_automatic_monitoring_in_background() -> None:
    """Runs on Starlette's background-task thread, after the response
    has already been sent -- mirrors `atlas.alpha.portfolio.api.router
    ._run_bulk_enrichment_in_background`'s own documented reason for
    building a fresh `Engine` here rather than reusing the request-scoped
    one: that `Engine` is bound to the request-handling thread, and
    reusing it from this separate thread would raise a real sqlite3
    threading error. `trigger_automatic_run` (not `run`) is used
    deliberately -- best-effort, never blocks this background task
    waiting for an unrelated in-progress run."""
    engine = get_decision_engine()
    build_monitoring_service(engine).trigger_automatic_run()


@router.get("", response_model=list[WatchlistEntryView])
def list_watchlist(
    service: AlphaWatchlistService = Depends(get_alpha_watchlist_service),
) -> list[WatchlistEntryView]:
    return [WatchlistEntryView.from_domain(entry) for entry in service.list_all()]


@router.get("/summary", response_model=list[WatchlistEntrySummaryView])
def list_watchlist_summary(
    store: AlphaWatchlistStore = Depends(get_alpha_watchlist_store),
    composition_service: InvestmentCaseCompositionService = Depends(get_investment_case_composition_service),
) -> list[WatchlistEntrySummaryView]:
    """Everything a Watchlist list surface needs, composed once.

    Provider-free by construction, and deliberately so. The two
    dependencies are the Watchlist store and the composition service;
    neither takes a provider, a quota tracker or a refresh coordinator,
    and nothing here writes. Note it reads `get_alpha_watchlist_store`
    rather than `get_alpha_watchlist_service` -- the service pulls in
    business-data providers and the identity gate for the *add* path's
    enrichment, which a read has no business touching.

    Deliberately `build`, not `build_many`, despite `build_many` being
    the batched read `portfolio_cockpit` uses. `build_many` resolves a
    Case's ticker only from a Portfolio holding -- its own docstring
    says the Watchlist path exists "in `build`, never `build_many`" --
    and passes `business_records=()` for any Case without a holding.
    A watchlist-only prospect would therefore come back analysed from
    no company data at all: no name, and a coverage and recommendation
    level describing an empty record set rather than what Atlas knows.
    Correct semantics outrank a cheaper read, so this pays four table
    scans per Case instead. That is a database cost, not a provider
    cost, and it replaces one provider-touching HTTP call per entry.

    A Case that does not resolve is simply absent from the response --
    `build`'s own honest-absence contract, carried through. The caller
    shows an unknown state for it rather than an invented one.

    Composition only: `describe_recommendation` reads the gate result
    the composition already carries, and `analysis_coverage` is read
    off it verbatim. No evaluator runs here, and no analysis is
    recomputed.
    """
    summaries: list[WatchlistEntrySummaryView] = []
    for entry in store.list_all():
        composition = composition_service.build(entry.case_id)
        if composition is None:
            continue
        analysis = composition.canonical_analysis
        profile = composition.company_profile
        summaries.append(
            WatchlistEntrySummaryView(
                ticker=entry.ticker,
                case_id=entry.case_id,
                added_at=entry.added_at,
                company_name=profile.name if profile is not None else None,
                sector=profile.sector if profile is not None else None,
                decision_support_level=describe_recommendation(analysis.recommendation).level.value,
                analysis_coverage_level=analysis.analysis_coverage.level.value,
            )
        )
    return summaries


@router.post("", response_model=WatchlistEntryView, status_code=201)
def add_watchlist_ticker(
    payload: AddWatchlistTickerRequestBody,
    background_tasks: BackgroundTasks,
    service: AlphaWatchlistService = Depends(get_alpha_watchlist_service),
) -> WatchlistEntryView:
    try:
        entry = service.add_ticker(payload.ticker)
    except AlphaWatchlistValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    background_tasks.add_task(_trigger_automatic_monitoring_in_background)
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
