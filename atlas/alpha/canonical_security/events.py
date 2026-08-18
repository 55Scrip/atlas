"""Domain events for the Canonical Security Foundation -- Sprint M
Phase 8's own seven-event list, implemented as plain frozen dataclasses.

"Publish nothing externally yet" (Sprint M Phase 8): these are data
shapes only. Nothing in this package constructs them automatically as a
side effect of calling an aggregate method, and there is no event bus,
dispatcher, or persistence wiring here -- a future service layer (the
Resolver Sprint K/L designed) is what would actually construct and
record these, once it exists. `tests/unit/alpha/canonical_security/
test_events.py` proves each shape is constructible and carries the
fields Sprint L Phase 12 specified; it does not, and could not yet,
prove anything about how they get produced in practice.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.canonical_security.value_objects import (
    IdentityConfidence,
    ProviderName,
    ResolutionStatus,
    VerificationStatus,
)


@dataclass(frozen=True)
class CanonicalSecurityCreated:
    canonical_security_id: str
    canonical_company_name: str
    native_ticker: str
    created_at: datetime


@dataclass(frozen=True)
class ProviderMappingAdded:
    canonical_security_id: str
    provider_name: ProviderName
    provider_ticker: str
    confidence: IdentityConfidence
    mapped_at: datetime


@dataclass(frozen=True)
class ProviderMappingVerified:
    """Recorded when a mapping's `verification_status` changes as a
    result of independent corroboration or dispute -- distinct from
    `ProviderMappingAdded`, which only records the mapping's initial
    creation."""

    canonical_security_id: str
    provider_name: ProviderName
    provider_ticker: str
    verification_status: VerificationStatus
    verified_at: datetime


@dataclass(frozen=True)
class ResolutionStatusChanged:
    canonical_security_id: str
    previous_status: ResolutionStatus
    new_status: ResolutionStatus
    changed_at: datetime


@dataclass(frozen=True)
class SecurityMerged:
    losing_canonical_security_id: str
    winning_canonical_security_id: str
    merged_at: datetime
    reason: str


@dataclass(frozen=True)
class SecuritySuperseded:
    old_canonical_security_id: str
    new_canonical_security_id: str
    superseded_at: datetime
    reason: str


@dataclass(frozen=True)
class SecurityRevoked:
    canonical_security_id: str
    revoked_at: datetime
    reason: str
