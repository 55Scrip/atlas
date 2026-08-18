"""The `CanonicalSecurity` aggregate root and its child value objects
(`ListingRef`, `ProviderMapping`, `SecurityIdentifier`) -- Sprint L
Phases 2-5, implemented exactly to that design.

Immutability discipline: `CanonicalSecurity` is a frozen dataclass, same
as `atlas.core.domain.case.entity.Case` and every other aggregate in this
codebase. "Mappings must be immutable except through aggregate methods"
(Sprint M Phase 4) is implemented literally -- every mutating-looking
method (`add_listing`, `add_provider_mapping`, `transition_to`) is a pure
function that returns a *new* `CanonicalSecurity`, never mutates `self`.
There is no way to change a field on an existing instance from outside
this module; `dataclasses.replace` inside these methods is the only path,
and every one of them re-validates the aggregate's invariants before
returning.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from atlas.alpha.canonical_security.exceptions import (
    CanonicalStatusRequiresListingError,
    DuplicateListingError,
    DuplicateProviderMappingError,
    EmptyTickerError,
)
from atlas.alpha.canonical_security.lifecycle import validate_transition
from atlas.alpha.canonical_security.value_objects import (
    CanonicalSecurityId,
    IdentifierType,
    IdentityConfidence,
    ListingRelationship,
    MicCode,
    ProviderName,
    ResolutionStatus,
    SecurityType,
    TradingCurrency,
    VerificationStatus,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ListingRef:
    """One tradeable instrument for a CanonicalSecurity -- a native
    listing, an ADR, a GDR, or an OTC line. Sprint J Phase 10's own
    design decision, restated as an enforced type: native and ADR
    listings are always separate `ListingRef` entries under one
    `CanonicalSecurity`, never merged into a single record and never
    silently substituted for one another."""

    ticker: str
    exchange_mic: MicCode
    currency: TradingCurrency
    relationship: ListingRelationship
    security_type: SecurityType
    provider_symbol: str | None = None

    def __post_init__(self) -> None:
        if not self.ticker or not self.ticker.strip():
            raise EmptyTickerError("ListingRef.ticker")


@dataclass(frozen=True)
class ProviderMapping:
    """One provider's claim about a security's identity -- Sprint L
    Phase 5. `confidence` and `verification_status` are per-mapping, not
    aggregate-level: a single CanonicalSecurity can hold one
    `CORROBORATED`/`HIGH` mapping and one `REJECTED` mapping
    simultaneously (the exact live shape of the `MC`/`EVO` collisions
    Sprints H/I found -- one provider's candidate accepted, another's
    rejected, both retained for audit)."""

    provider_name: ProviderName
    provider_ticker: str
    confidence: IdentityConfidence
    verification_status: VerificationStatus
    mapped_at: datetime
    provider_security_id: str | None = None
    provider_exchange_code: str | None = None
    verified_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.provider_ticker or not self.provider_ticker.strip():
            raise EmptyTickerError("ProviderMapping.provider_ticker")


@dataclass(frozen=True)
class SecurityIdentifier:
    """One alternate identifier (ISIN/FIGI/CUSIP/SEDOL/CIK) recorded
    opportunistically -- Sprint J Phase 4: never required for `CANONICAL`
    status, since none of these were obtainable on any live-tested
    provider tier through Sprint I."""

    identifier_type: IdentifierType
    value: str
    recorded_at: datetime


@dataclass(frozen=True)
class CanonicalSecurity:
    """The aggregate root. Owns identity only -- never market data,
    financial facts, analysis results, or recommendation state (Sprint L
    Phase 2's own ownership boundary).

    Invariants enforced by this class's own methods, not just at
    construction (Sprint L Phase 2, restated):

    1. A CanonicalSecurity in `CANONICAL` or `ACTIVE` status must have at
       least one listing -- enforced in `transition_to`.
    2. No two listings may share the same `(exchange_mic, ticker)` pair
       -- enforced in `add_listing`.
    3. No two *active* (non-`SUPERSEDED_MAPPING`) provider mappings may
       share the same `(provider_name, provider_ticker)` pair --
       enforced in `add_provider_mapping`.
    4. `id` is immutable for the aggregate's entire lifetime, including
       across `SUPERSEDED`/`MERGED` transitions -- structurally
       guaranteed since no method in this class ever replaces `id`.
    """

    id: CanonicalSecurityId
    canonical_company_name: str
    native_ticker: str
    primary_exchange_mic: MicCode
    country: str
    trading_currency: TradingCurrency
    resolution_status: ResolutionStatus
    listings: tuple[ListingRef, ...] = field(default_factory=tuple)
    provider_mappings: tuple[ProviderMapping, ...] = field(default_factory=tuple)
    identifiers: tuple[SecurityIdentifier, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.native_ticker or not self.native_ticker.strip():
            raise EmptyTickerError("CanonicalSecurity.native_ticker")
        if not self.canonical_company_name or not self.canonical_company_name.strip():
            raise ValueError("CanonicalSecurity.canonical_company_name must not be blank")

    @classmethod
    def discover(
        cls,
        *,
        canonical_company_name: str,
        native_ticker: str,
        primary_exchange_mic: MicCode,
        country: str,
        trading_currency: TradingCurrency,
        clock=_utc_now,
    ) -> CanonicalSecurity:
        """Establish a brand-new CanonicalSecurity in `DISCOVERED`
        status -- the entry point for a resolution attempt, before any
        candidate has been found. Named `discover`, not `create`, to
        match Sprint L Phase 6's own vocabulary for this first state."""
        now = clock()
        return cls(
            id=CanonicalSecurityId(),
            canonical_company_name=canonical_company_name,
            native_ticker=native_ticker,
            primary_exchange_mic=primary_exchange_mic,
            country=country,
            trading_currency=trading_currency,
            resolution_status="DISCOVERED",
            created_at=now,
            updated_at=now,
        )

    @property
    def primary_listing(self) -> ListingRef | None:
        """The `NATIVE`-relationship listing if one exists, else the
        sole listing if only one was ever resolved (e.g. an ADR-only
        resolution, per Sprint L Phase 3's own definition), else `None`
        for an aggregate that has no listings yet."""
        for listing in self.listings:
            if listing.relationship == "NATIVE":
                return listing
        return self.listings[0] if len(self.listings) == 1 else None

    def add_listing(self, listing: ListingRef, *, clock=_utc_now) -> CanonicalSecurity:
        """Append a new listing. Listings are append-only -- never
        overwritten (Sprint J Phase 4) -- and never duplicated on the
        same `(exchange_mic, ticker)` pair."""
        for existing in self.listings:
            if existing.exchange_mic == listing.exchange_mic and existing.ticker == listing.ticker:
                raise DuplicateListingError(str(listing.exchange_mic.value), listing.ticker)
        return replace(self, listings=self.listings + (listing,), updated_at=clock())

    def add_provider_mapping(self, mapping: ProviderMapping, *, clock=_utc_now) -> CanonicalSecurity:
        """Append a new provider mapping. Rejects a duplicate
        `(provider_name, provider_ticker)` pair among mappings that are
        still active (i.e. not already `SUPERSEDED_MAPPING`) -- a
        changed mapping must be recorded as a new row with the old one
        explicitly superseded first, never silently overwritten in
        place (Sprint L Phase 11)."""
        for existing in self.provider_mappings:
            if (
                existing.provider_name == mapping.provider_name
                and existing.provider_ticker == mapping.provider_ticker
                and existing.verification_status != "SUPERSEDED_MAPPING"
            ):
                raise DuplicateProviderMappingError(mapping.provider_name, mapping.provider_ticker)
        return replace(self, provider_mappings=self.provider_mappings + (mapping,), updated_at=clock())

    def add_identifier(self, identifier: SecurityIdentifier, *, clock=_utc_now) -> CanonicalSecurity:
        """Append an alternate identifier (Sprint J Phase 4) -- append-
        only, same discipline as listings and mappings."""
        return replace(self, identifiers=self.identifiers + (identifier,), updated_at=clock())

    def transition_to(self, requested: ResolutionStatus, *, clock=_utc_now) -> CanonicalSecurity:
        """The one path to changing `resolution_status`. Validates the
        transition against `lifecycle.py`'s legal-transition table, and
        additionally enforces the CANONICAL/ACTIVE listing invariant
        (Sprint L Phase 2) before allowing either of those two specific
        target statuses."""
        validate_transition(self.resolution_status, requested)
        if requested in ("CANONICAL", "ACTIVE") and not self.listings:
            raise CanonicalStatusRequiresListingError(requested)
        return replace(self, resolution_status=requested, updated_at=clock())
