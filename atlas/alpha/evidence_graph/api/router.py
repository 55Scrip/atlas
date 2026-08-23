"""REST controller for the Evidence Graph (Atlas Intelligence Sprint
10). A new top-level prefix, matching `monitoring`/`ingestion`'s own
precedent.

`GET /evidence-graph/{case_id}` -- the full graph plus its weak
dependencies plus a compact summary (Deliverable 6's own "kompakt,
progressivt"). No separate impact/support endpoints: a Case's own
graph is small enough (dozens, not thousands, of nodes) that a caller
wanting "what does this affect" or "follow the support backward" can
walk the already-returned edge list itself -- adding a second round
trip per query would not be simpler, only slower.

`GET /evidence-graph/portfolio/shared-weak-points` -- Deliverable 7,
registered *before* the `{case_id}` route below so `"portfolio"` is
never swallowed as a case id (FastAPI matches in registration order).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from atlas.alpha.evidence_graph.api.dependencies import get_evidence_graph_service
from atlas.alpha.evidence_graph.api.schemas import (
    EvidenceGraphComparisonView,
    EvidenceGraphView,
    PortfolioSharedWeakPointsView,
)
from atlas.alpha.evidence_graph.service import EvidenceGraphService

router = APIRouter(prefix="/evidence-graph", tags=["evidence-graph"])


@router.get("/portfolio/shared-weak-points", response_model=PortfolioSharedWeakPointsView)
def get_portfolio_shared_weak_points(
    service: EvidenceGraphService = Depends(get_evidence_graph_service),
) -> PortfolioSharedWeakPointsView:
    return PortfolioSharedWeakPointsView.from_domain(service.portfolio_shared_weak_points())


@router.get("/compare", response_model=EvidenceGraphComparisonView)
def compare_evidence_graph(
    ticker_a: str = Query(alias="tickerA"),
    ticker_b: str = Query(alias="tickerB"),
    service: EvidenceGraphService = Depends(get_evidence_graph_service),
) -> EvidenceGraphComparisonView:
    comparison = service.compare(ticker_a, ticker_b)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return EvidenceGraphComparisonView.from_domain(comparison)


@router.get("/{case_id}", response_model=EvidenceGraphView)
def get_evidence_graph(case_id: str, service: EvidenceGraphService = Depends(get_evidence_graph_service)) -> EvidenceGraphView:
    built = service.build_for_case(case_id)
    if built is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return EvidenceGraphView.from_domain(built.graph, built.weak_dependencies, built.impacted_changes)
