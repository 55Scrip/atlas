"""HTTP schemas for Security Confirmation (Sprint 20). CamelCase via
the shared Core `CamelModel` (ADR-004), matching every other Alpha
schema module.

`ConfirmSecurityRequest.discoveryMethod`/`source` are plain strings,
not enums re-derived from `atlas.alpha.security_discovery.models`
(that package's `DiscoveryMethod` literal) -- this API accepts and
carries through whatever the caller (a future confirmation UI, or a
script driving one) asserts, validated at the service layer against
the one closed allow-list that actually exists
(`service._SUPPORTED_DISCOVERY_SOURCES`), never re-imported here as a
type dependency between two otherwise-independent Alpha packages.
"""
from __future__ import annotations

from datetime import datetime

from atlas.alpha.security_confirmation.models import ConfirmedSecuritySelection
from atlas.core.infrastructure.api.serialization import CamelModel


class ConfirmSecurityRequest(CamelModel):
    ticker: str
    display_name: str
    cik: int | None = None
    discovery_method: str
    source: str


class ConfirmedSecuritySelectionView(CamelModel):
    id: str
    decision_id: str
    confirmed_ticker: str
    confirmed_display_name: str
    confirmed_cik: int | None
    discovery_method: str
    discovery_source: str
    confirmed_at: datetime

    @classmethod
    def from_domain(cls, selection: ConfirmedSecuritySelection) -> "ConfirmedSecuritySelectionView":
        return cls(
            id=selection.id,
            decision_id=selection.decision_id,
            confirmed_ticker=selection.confirmed_ticker,
            confirmed_display_name=selection.confirmed_display_name,
            confirmed_cik=selection.confirmed_cik,
            discovery_method=selection.discovery_method,
            discovery_source=selection.discovery_source,
            confirmed_at=selection.confirmed_at,
        )
