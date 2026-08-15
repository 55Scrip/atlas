"""HTTP schema for Security Identity Evidence (Sprint 23). CamelCase
via the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module. No request body -- `POST .../verify` takes no payload,
it always verifies whatever is currently confirmed for the Decision.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.security_identity_evidence.models import SecurityIdentityEvidence, SecurityVerificationStatus
from atlas.core.infrastructure.api.serialization import CamelModel


class SecurityIdentityEvidenceView(CamelModel):
    id: str
    confirmation_id: str
    provider: str
    status: SecurityVerificationStatus
    provider_identifier: str | None
    verified_ticker: str | None
    verified_name: str | None
    exchange: str | None
    verified_at: datetime

    @classmethod
    def from_domain(cls, evidence: SecurityIdentityEvidence) -> "SecurityIdentityEvidenceView":
        return cls(
            id=evidence.id,
            confirmation_id=evidence.confirmation_id,
            provider=evidence.provider,
            status=evidence.status,
            provider_identifier=evidence.provider_identifier,
            verified_ticker=evidence.verified_ticker,
            verified_name=evidence.verified_name,
            exchange=evidence.exchange,
            verified_at=evidence.verified_at,
        )
