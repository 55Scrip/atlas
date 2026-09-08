"""Resolve an Investment Case for a security, without membership.

POST /case-identity/ensure  {"ticker": "ASML"}  ->  {"caseId": "..."}

This is the endpoint Discovery and Search need. Before Sprint 4A a Case
had no instrument of its own, so the only way to get an analysable one
was to add the company to the Watchlist -- which made "I want to look
at this" indistinguishable from "monitor this for me". Opening a Case
is now just opening a Case.

It creates exactly one thing: Case identity, plus its instrument
binding, through the canonical `CaseGenerationService`. No Watchlist
membership, no Portfolio holding, no Decision Memory event, no
recommendation, no provider call. An existing Case for the ticker is
reused, so repeated opens never duplicate.

The ticker is upper-cased and trimmed and otherwise passed through
untouched -- the same operative key the rest of Alpha uses. No
normalization is invented here: that is how `SU.PA` (Schneider
Electric, Euronext Paris) would come to share a Case with `SU` (Suncor
Energy, NYSE), and both are in this database.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.case_instrument.exceptions import ConflictingCaseInstrumentBindingError
from atlas.alpha.portfolio.api.dependencies import get_case_generation_service
from atlas.core.infrastructure.api.serialization import CamelModel

router = APIRouter(prefix="/case-identity", tags=["case-identity"])


class EnsureCaseRequestBody(CamelModel):
    ticker: str


class EnsureCaseResponse(CamelModel):
    case_id: str
    ticker: str


@router.post("/ensure", response_model=EnsureCaseResponse)
def ensure_case_for_ticker(
    payload: EnsureCaseRequestBody,
    service: CaseGenerationService = Depends(get_case_generation_service),
) -> EnsureCaseResponse:
    ticker = payload.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker must not be blank")
    try:
        case_id = service.ensure_case_id(current_case_id=None, ticker=ticker)
    except ConflictingCaseInstrumentBindingError as error:
        # A Case already bound to a different instrument. Refused
        # loudly rather than rebound: moving a thesis and its history
        # onto another security is not something to do quietly.
        raise HTTPException(status_code=409, detail=str(error)) from error
    return EnsureCaseResponse(case_id=case_id, ticker=ticker)
