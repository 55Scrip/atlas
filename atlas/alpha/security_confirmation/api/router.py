"""REST controller for Security Confirmation (Sprint 20).

POST /decisions/{decision_id}/security-confirmation  -- record an
    explicit investor confirmation for one Decision.
GET  /decisions/{decision_id}/security-confirmation   -- read it back.

Decision-scoped only, deliberately -- Sprint 20's own scope
investigation found no other scope (Case, subject-string, investor-
global alias) provably safe; see this package's own `__init__.py`.
Nested under `/decisions/{decision_id}/...` rather than a flat
`/security-confirmations` resource specifically so the URL itself
carries the scope, rather than relying on callers to remember it.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

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
