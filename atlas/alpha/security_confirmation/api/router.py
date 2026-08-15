"""REST controller for Security Confirmation (Sprint 20; Correction &
Revocation added Sprint 22).

POST   /decisions/{decision_id}/security-confirmation          -- record
    an explicit investor confirmation for one Decision (first-time
    confirmation only; a different ticker while one is active is a
    409 conflict, unchanged since Sprint 20 -- see `service.confirm`).
GET    /decisions/{decision_id}/security-confirmation           -- read
    the current confirmation back, if any.
POST   /decisions/{decision_id}/security-confirmation/correct   -- the
    one explicit "change my confirmed selection" action (Sprint 22):
    requires a current confirmation to exist, appends a revocation of
    it plus a fresh confirmation, never deletes or overwrites the
    original event.
POST   /decisions/{decision_id}/security-confirmation/revoke    -- the
    explicit "I no longer stand behind my current confirmation" action
    (Sprint 22); idempotent no-op if nothing is currently confirmed.

Decision-scoped only, deliberately -- Sprint 20's own scope
investigation found no other scope (Case, subject-string, investor-
global alias) provably safe; see this package's own `__init__.py`.
Nested under `/decisions/{decision_id}/...` rather than a flat
`/security-confirmations` resource specifically so the URL itself
carries the scope, rather than relying on callers to remember it.

No `DELETE` endpoint exists, deliberately (Sprint 22 Phase 9): nothing
this package writes is ever actually deleted, so a `DELETE` verb would
misdescribe what `revoke` really does -- append a new event, not erase
the old one.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from atlas.alpha.security_confirmation.api.dependencies import get_confirm_security_selection_service
from atlas.alpha.security_confirmation.api.schemas import (
    ConfirmedSecuritySelectionView,
    ConfirmSecurityRequest,
)
from atlas.alpha.security_confirmation.service import (
    ConfirmSecuritySelectionRequest,
    ConfirmSecuritySelectionService,
)

router = APIRouter(prefix="/decisions/{decision_id}/security-confirmation", tags=["security-confirmation"])


@router.post("", response_model=ConfirmedSecuritySelectionView, status_code=201)
def confirm_security_selection(
    decision_id: str,
    payload: ConfirmSecurityRequest,
    service: ConfirmSecuritySelectionService = Depends(get_confirm_security_selection_service),
) -> ConfirmedSecuritySelectionView:
    selection = service.confirm(
        ConfirmSecuritySelectionRequest(
            decision_id=decision_id,
            confirmed_ticker=payload.ticker,
            confirmed_display_name=payload.display_name,
            confirmed_cik=payload.cik,
            discovery_method=payload.discovery_method,
            discovery_source=payload.source,
        )
    )
    return ConfirmedSecuritySelectionView.from_domain(selection)


@router.get("", response_model=ConfirmedSecuritySelectionView)
def get_security_confirmation(
    decision_id: str,
    service: ConfirmSecuritySelectionService = Depends(get_confirm_security_selection_service),
) -> ConfirmedSecuritySelectionView:
    selection = service.get(decision_id)
    if selection is None:
        raise HTTPException(status_code=404, detail="No security confirmation recorded for this Decision")
    return ConfirmedSecuritySelectionView.from_domain(selection)


@router.post("/correct", response_model=ConfirmedSecuritySelectionView)
def correct_security_selection(
    decision_id: str,
    payload: ConfirmSecurityRequest,
    service: ConfirmSecuritySelectionService = Depends(get_confirm_security_selection_service),
) -> ConfirmedSecuritySelectionView:
    selection = service.correct(
        ConfirmSecuritySelectionRequest(
            decision_id=decision_id,
            confirmed_ticker=payload.ticker,
            confirmed_display_name=payload.display_name,
            confirmed_cik=payload.cik,
            discovery_method=payload.discovery_method,
            discovery_source=payload.source,
        )
    )
    return ConfirmedSecuritySelectionView.from_domain(selection)


@router.post("/revoke", status_code=204, response_class=Response)
def revoke_security_selection(
    decision_id: str,
    service: ConfirmSecuritySelectionService = Depends(get_confirm_security_selection_service),
) -> Response:
    service.revoke(decision_id)
    return Response(status_code=204)
