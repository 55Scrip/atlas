"""REST controller for the Evidence Timeline (Atlas Intelligence
Sprint 5). A new, sibling top-level prefix, matching how `stance`/
`explainability`/`evidence-quality` themselves introduced their own
prefix for a genuinely new report.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.evidence_timeline.api.dependencies import get_evidence_timeline_service
from atlas.alpha.evidence_timeline.api.schemas import EvidenceTimelineEntryPairView, EvidenceTimelineFeedView, EvidenceSnapshotView, EvidenceHistoryView
from atlas.alpha.evidence_timeline.service import EvidenceTimelineService

router = APIRouter(prefix="/evidence-timeline", tags=["evidence-timeline"])


def _pairs_view(pairs: tuple) -> list[EvidenceTimelineEntryPairView]:
    return [
        EvidenceTimelineEntryPairView(snapshot=EvidenceSnapshotView.from_domain(snapshot), history=EvidenceHistoryView.from_domain(history))
        for snapshot, history in pairs
    ]


@router.get("/case/{case_id}", response_model=list[EvidenceTimelineEntryPairView])
def get_evidence_timeline_for_case(
    case_id: str, service: EvidenceTimelineService = Depends(get_evidence_timeline_service)
) -> list[EvidenceTimelineEntryPairView]:
    return _pairs_view(service.history_for_case(case_id))


@router.get("/ticker/{ticker}", response_model=list[EvidenceTimelineEntryPairView])
def get_evidence_timeline_for_ticker(
    ticker: str, service: EvidenceTimelineService = Depends(get_evidence_timeline_service)
) -> list[EvidenceTimelineEntryPairView]:
    pairs = service.history_for_ticker(ticker)
    if pairs is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for this ticker")
    return _pairs_view(pairs)


@router.get("/feed", response_model=EvidenceTimelineFeedView)
def get_evidence_timeline_feed(service: EvidenceTimelineService = Depends(get_evidence_timeline_service)) -> EvidenceTimelineFeedView:
    """Deliverables 6/7/9 -- the unified, cross-Case timeline Portfolio/
    Discovery/Daily Brief read from."""
    return EvidenceTimelineFeedView.from_domain(service.build_feed())
