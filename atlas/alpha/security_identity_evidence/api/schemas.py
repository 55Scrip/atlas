"""HTTP schema for Security Identity Evidence (Sprint 23). CamelCase
via the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module. No request body -- `POST .../verify` takes no payload,
it always verifies whatever is currently confirmed for the Decision.

`SecurityConfirmationHistoryEntryView` (Sprint 24) is the response
shape for the new read-only `GET .../history` endpoint -- see
`router.py`'s own docstring for why this exists. It carries
`eventType` (never exposed by `security_confirmation`'s own
`ConfirmedSecuritySelectionView`, which only ever represents "current"
state) precisely because history needs to distinguish a `"confirmed"`
row from a `"revoked"` one; each entry nests the evidence gathered
against *that specific* confirmation event, never evidence from any
other event.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.security_confirmation.models import SecurityConfirmationEvent, SecurityConfirmationEventType
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


class SecurityConfirmationHistoryEntryView(CamelModel):
    id: str
    event_type: SecurityConfirmationEventType
    confirmed_ticker: str
    confirmed_display_name: str
    confirmed_cik: int | None
    discovery_method: str
    discovery_source: str
    recorded_at: datetime
    evidence: list[SecurityIdentityEvidenceView]

    @classmethod
    def from_domain(
        cls, event: SecurityConfirmationEvent, evidence: list[SecurityIdentityEvidence]
    ) -> "SecurityConfirmationHistoryEntryView":
        return cls(
            id=event.id,
            event_type=event.event_type,
            confirmed_ticker=event.confirmed_ticker,
            confirmed_display_name=event.confirmed_display_name,
            confirmed_cik=event.confirmed_cik,
            discovery_method=event.discovery_method,
            discovery_source=event.discovery_source,
            recorded_at=event.recorded_at,
            evidence=[SecurityIdentityEvidenceView.from_domain(item) for item in evidence],
        )
