"""REST controller for Security Identity Evidence (Sprint 23).

POST /decisions/{decision_id}/security-confirmation/verify        --
    the one explicit "check external evidence" action. Always
    verifies whatever is *currently* confirmed for the Decision;
    never triggered automatically by confirm/correct/revoke (Sprint 23
    ground rule 8/9/14).
GET  /decisions/{decision_id}/security-confirmation/verification   --
    reads back the latest verification attempt for the current
    confirmation, if any.

Nested under the same `/decisions/{decision_id}/security-confirmation`
prefix `security_confirmation`'s own router already owns, matching
that package's own reasoning for putting scope in the URL rather than
relying on callers to remember it -- this package never registers its
own top-level prefix.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from atlas.alpha.security_confirmation.api.dependencies import get_security_confirmation_repository
from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_identity_evidence.api.dependencies import (
    get_security_identity_evidence_repository,
    get_security_verification_service,
)
from atlas.alpha.security_identity_evidence.api.schemas import SecurityIdentityEvidenceView
from atlas.alpha.security_identity_evidence.repository import SqlAlchemySecurityIdentityEvidenceRepository
from atlas.alpha.security_identity_evidence.service import SecurityVerificationService

router = APIRouter(prefix="/decisions/{decision_id}/security-confirmation", tags=["security-identity-evidence"])


@router.post("/verify", response_model=SecurityIdentityEvidenceView, status_code=201)
def verify_security_selection(
    decision_id: str,
    service: SecurityVerificationService = Depends(get_security_verification_service),
) -> SecurityIdentityEvidenceView:
    evidence = service.verify(decision_id)
    return SecurityIdentityEvidenceView.from_domain(evidence)


@router.get("/verification", response_model=SecurityIdentityEvidenceView)
def get_security_verification(
    decision_id: str,
    confirmation_repository: SqlAlchemySecurityConfirmationRepository = Depends(
        get_security_confirmation_repository
    ),
    evidence_repository: SqlAlchemySecurityIdentityEvidenceRepository = Depends(
        get_security_identity_evidence_repository
    ),
) -> SecurityIdentityEvidenceView:
    confirmation = confirmation_repository.get_by_decision_id(decision_id)
    if confirmation is None:
        raise HTTPException(status_code=404, detail="No security confirmation recorded for this Decision")
    evidence = evidence_repository.get_latest(confirmation.id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="No verification attempt recorded for this confirmation")
    return SecurityIdentityEvidenceView.from_domain(evidence)
