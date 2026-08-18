"""Value objects for the Canonical Security Foundation.

Every closed-vocabulary field (`ProviderName`, `IdentityConfidence`,
`VerificationStatus`, `ResolutionStatus`, `SecurityType`,
`ListingRelationship`) is a `Literal` plus a `validate_*` function that
checks membership in an explicit frozenset -- the same "closed allow-list,
grows only when a real capability is built" discipline already
established by `atlas.alpha.security_confirmation.service`'s own
`_SUPPORTED_DISCOVERY_SOURCES`. A `Literal` alone gives no runtime
protection against a typo'd string reaching the aggregate; these
functions are what actually enforce Sprint L Phase 4/5's identifier and
provider vocabulary at construction time, not just at the type-checker
level.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

from atlas.alpha.canonical_security.exceptions import (
    InvalidExchangeCodeError,
    InvalidMicCodeError,
    InvalidTradingCurrencyError,
    UnsupportedIdentifierTypeError,
    UnsupportedIdentityConfidenceError,
    UnsupportedListingRelationshipError,
    UnsupportedProviderNameError,
    UnsupportedResolutionStatusError,
    UnsupportedSecurityTypeError,
    UnsupportedVerificationStatusError,
)


@dataclass(frozen=True)
class CanonicalSecurityId:
    """Identity of a CanonicalSecurity. Generated once, at creation, and
    never reused -- same pattern as `atlas.core.domain.case.value_
    objects.CaseId`, since a CanonicalSecurity is exactly the same kind
    of thing structurally: an aggregate root identified by a UUID that
    outlives every other field on the aggregate, including across
    SUPERSEDED/MERGED transitions (the id itself is never reassigned)."""

    value: uuid.UUID = field(default_factory=uuid.uuid4)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ExchangeCode:
    """A provider's own display label for an exchange (e.g. Twelve
    Data's `"OMX"`). Deliberately distinct from `MicCode` -- see Sprint
    J Phase 5: providers use inconsistent display strings for the same
    standardized exchange, and this codebase must never compare them as
    if they were the same kind of value."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidExchangeCodeError(self.value)


@dataclass(frozen=True)
class MicCode:
    """A standardized ISO 10383 Market Identifier Code (e.g. `XSTO` for
    OMX Stockholm, `XNGS` for Nasdaq). Normalized to uppercase since a
    MIC is not case-sensitive identity information -- two candidates
    differing only in case must compare equal, never be treated as a
    mismatch."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidMicCodeError(self.value)
        object.__setattr__(self, "value", self.value.strip().upper())


@dataclass(frozen=True)
class TradingCurrency:
    """A 3-letter currency code (e.g. `SEK`, `USD`). Deliberately not
    validated against a fixed ISO 4217 list -- Atlas has no such list
    anywhere else in the codebase (see Sprint J Phase 14's own currency-
    safety audit), and inventing one here would be new scope beyond this
    sprint's foundation. Structural validation only: exactly three
    alphabetic characters, normalized to uppercase."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper() if self.value else ""
        if len(normalized) != 3 or not normalized.isalpha():
            raise InvalidTradingCurrencyError(self.value)
        object.__setattr__(self, "value", normalized)


SecurityType = Literal["COMMON_STOCK", "DEPOSITARY_RECEIPT", "ETF", "OTHER"]
_SECURITY_TYPES: frozenset[str] = frozenset({"COMMON_STOCK", "DEPOSITARY_RECEIPT", "ETF", "OTHER"})


def validate_security_type(value: str) -> SecurityType:
    if value not in _SECURITY_TYPES:
        raise UnsupportedSecurityTypeError(value)
    return value  # type: ignore[return-value]


ListingRelationship = Literal["NATIVE", "ADR", "GDR", "OTC"]
_LISTING_RELATIONSHIPS: frozenset[str] = frozenset({"NATIVE", "ADR", "GDR", "OTC"})


def validate_listing_relationship(value: str) -> ListingRelationship:
    if value not in _LISTING_RELATIONSHIPS:
        raise UnsupportedListingRelationshipError(value)
    return value  # type: ignore[return-value]


#: Closed allow-list, Sprint L Phase 5's four named providers -- grows
#: only when a real adapter is actually built (matching the discipline
#: `security_confirmation`'s own discovery-source allow-list already
#: established). OpenFIGI is a first-class provider here, not just a
#: verification detail, per Sprint L Phase 5's explicit instruction.
ProviderName = Literal["SEC_EDGAR", "ALPHA_VANTAGE", "TWELVE_DATA", "OPENFIGI"]
_PROVIDER_NAMES: frozenset[str] = frozenset({"SEC_EDGAR", "ALPHA_VANTAGE", "TWELVE_DATA", "OPENFIGI"})


def validate_provider_name(value: str) -> ProviderName:
    if value not in _PROVIDER_NAMES:
        raise UnsupportedProviderNameError(value)
    return value  # type: ignore[return-value]


#: Sprint J Phase 8's four-level model -- confidence must never be
#: computed from ticker equality alone (enforced by the Resolver this
#: aggregate will eventually sit behind, not by this value object
#: itself, which only records the outcome).
IdentityConfidence = Literal["HIGH", "MEDIUM", "LOW", "REJECTED"]
_IDENTITY_CONFIDENCE_LEVELS: frozenset[str] = frozenset({"HIGH", "MEDIUM", "LOW", "REJECTED"})


def validate_identity_confidence(value: str) -> IdentityConfidence:
    if value not in _IDENTITY_CONFIDENCE_LEVELS:
        raise UnsupportedIdentityConfidenceError(value)
    return value  # type: ignore[return-value]


#: Per-mapping verification state (Sprint L Phase 5) -- distinct from
#: the aggregate-level `IdentityConfidence`: a single CanonicalSecurity
#: can hold one `CORROBORATED` mapping and one `REJECTED` mapping
#: simultaneously (e.g. Twelve Data corroborated, SEC EDGAR rejected for
#: the `MC`/`EVO` collision pattern).
VerificationStatus = Literal["UNVERIFIED", "CORROBORATED", "DISPUTED", "REJECTED", "SUPERSEDED_MAPPING"]
_VERIFICATION_STATUSES: frozenset[str] = frozenset(
    {"UNVERIFIED", "CORROBORATED", "DISPUTED", "REJECTED", "SUPERSEDED_MAPPING"}
)


def validate_verification_status(value: str) -> VerificationStatus:
    if value not in _VERIFICATION_STATUSES:
        raise UnsupportedVerificationStatusError(value)
    return value  # type: ignore[return-value]


#: Sprint L Phase 6's eleven-state lifecycle, plus `EXPIRED` (Sprint M's
#: own Phase 5 addition, covering Sprint L's "identity expires" remaining
#: unknown -- an `ACTIVE` security whose corroborating evidence has aged
#: out). See `lifecycle.py` for the legal-transition table this vocabulary
#: is checked against.
ResolutionStatus = Literal[
    "DISCOVERED",
    "CANDIDATES_FOUND",
    "IDENTITY_VERIFIED",
    "CONFIRMED",
    "CANONICAL",
    "ACTIVE",
    "REJECTED",
    "SUPERSEDED",
    "MERGED",
    "REVOKED",
    "EXPIRED",
]
_RESOLUTION_STATUSES: frozenset[str] = frozenset(
    {
        "DISCOVERED",
        "CANDIDATES_FOUND",
        "IDENTITY_VERIFIED",
        "CONFIRMED",
        "CANONICAL",
        "ACTIVE",
        "REJECTED",
        "SUPERSEDED",
        "MERGED",
        "REVOKED",
        "EXPIRED",
    }
)


def validate_resolution_status(value: str) -> ResolutionStatus:
    if value not in _RESOLUTION_STATUSES:
        raise UnsupportedResolutionStatusError(value)
    return value  # type: ignore[return-value]


#: Sprint J Phase 4's alternate-identifier types -- ISIN/FIGI/CUSIP/SEDOL
#: are alternate, opportunistic identifiers, never required for
#: `CANONICAL` status (see `models.py`'s aggregate invariants). CIK is
#: included here too, scoped explicitly to SEC-registered filers only
#: (Sprint J Phase 5: never treated as sufficient for a non-US company).
IdentifierType = Literal["ISIN", "FIGI", "CUSIP", "SEDOL", "CIK"]
_IDENTIFIER_TYPES: frozenset[str] = frozenset({"ISIN", "FIGI", "CUSIP", "SEDOL", "CIK"})


def validate_identifier_type(value: str) -> IdentifierType:
    if value not in _IDENTIFIER_TYPES:
        raise UnsupportedIdentifierTypeError(value)
    return value  # type: ignore[return-value]
