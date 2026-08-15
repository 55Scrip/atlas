"""Composition wiring for Security Identity Evidence. Same shared-engine
pattern every other repository's dependencies module uses, reusing
`security_confirmation`'s own `get_security_confirmation_repository`
for the read-only side of this package's one Alpha-to-Alpha dependency.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.engine import Engine

from atlas.alpha.security_confirmation.api.dependencies import get_security_confirmation_repository
from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_identity_evidence.repository import SqlAlchemySecurityIdentityEvidenceRepository
from atlas.alpha.security_identity_evidence.service import SecurityVerificationService
from atlas.alpha.security_identity_evidence.table import create_security_identity_evidence_table
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine


def get_security_identity_evidence_repository(
    engine: Engine = Depends(get_decision_engine),
) -> SqlAlchemySecurityIdentityEvidenceRepository:
    create_security_identity_evidence_table(engine)
    return SqlAlchemySecurityIdentityEvidenceRepository(engine)


def get_security_verification_service(
    confirmation_repository: SqlAlchemySecurityConfirmationRepository = Depends(
        get_security_confirmation_repository
    ),
    evidence_repository: SqlAlchemySecurityIdentityEvidenceRepository = Depends(
        get_security_identity_evidence_repository
    ),
) -> SecurityVerificationService:
    return SecurityVerificationService(confirmation_repository, evidence_repository)
