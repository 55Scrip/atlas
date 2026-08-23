"""REST controller for the Evidence Quality Engine (Atlas Intelligence
Sprint 4). A new, sibling top-level prefix, matching how `stance`/
`explainability` themselves introduced their own prefix for a genuinely
new report.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.evidence_quality.api.dependencies import get_evidence_quality_service
from atlas.alpha.evidence_quality.api.schemas import EvidenceQualityReportView, TickerEvidenceQualityView
from atlas.alpha.evidence_quality.service import EvidenceQualityService

router = APIRouter(prefix="/evidence-quality", tags=["evidence-quality"])


@router.get("/case/{case_id}", response_model=EvidenceQualityReportView)
def get_evidence_quality_for_case(
    case_id: str, service: EvidenceQualityService = Depends(get_evidence_quality_service)
) -> EvidenceQualityReportView:
    report = service.assess_for_case(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return EvidenceQualityReportView.from_domain(report)


@router.get("/ticker/{ticker}", response_model=EvidenceQualityReportView)
def get_evidence_quality_for_ticker(
    ticker: str, service: EvidenceQualityService = Depends(get_evidence_quality_service)
) -> EvidenceQualityReportView:
    report = service.assess_for_ticker(ticker)
    if report is None:
        raise HTTPException(status_code=404, detail="No Investment Case exists for this ticker")
    return EvidenceQualityReportView.from_domain(report)


@router.get("/holdings", response_model=list[TickerEvidenceQualityView])
def get_evidence_quality_for_holdings(
    service: EvidenceQualityService = Depends(get_evidence_quality_service),
) -> list[TickerEvidenceQualityView]:
    """Deliverable 6 -- Portfolio's own evidence-quality surface."""
    return [
        TickerEvidenceQualityView(ticker=ticker, report=EvidenceQualityReportView.from_domain(report))
        for ticker, report in service.assess_all_holdings()
    ]


@router.get("/candidates", response_model=list[TickerEvidenceQualityView])
def get_evidence_quality_for_candidates(
    service: EvidenceQualityService = Depends(get_evidence_quality_service),
) -> list[TickerEvidenceQualityView]:
    """Deliverable 7 -- Discovery's own evidence-aware candidate cards."""
    return [
        TickerEvidenceQualityView(ticker=ticker, report=EvidenceQualityReportView.from_domain(report))
        for ticker, report in service.assess_for_candidates()
    ]
