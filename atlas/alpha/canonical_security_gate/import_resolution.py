"""Turn what a broker exported into the security it actually refers to.

Everything this needs already existed and was proven separately: the import
captures an ISIN and a venue, the ISIN validator rejects malformed ones,
OpenFIGI answers an ISIN with the share class every listing of it agrees on,
the master holds share-class identifiers for 36 securities, and a security
can now be constructed without a proven currency. What did not exist was the
line joining them, so a Stockholm holding could be captured perfectly and
still resolve to nothing.

The order is the whole design, because the order is what keeps a weak
identifier from ever outranking a strong one:

1. **A valid ISIN, or nothing.** No ISIN and this resolver declines --
   without calling a provider, without creating anything. A ticker is not
   identity; that is the original defect, not a case to handle.
2. **The master, before the provider.** An ISIN already recorded against a
   security resolves it with zero network calls.
3. **The provider, for the share class.** An ISIN names hundreds of
   listings -- 209 for Volvo B -- so there is no "the" FIGI to pick. What
   every one of them agrees on is the share class, and that is what gets
   matched against the master next. This is where an already-known security
   is recognized through an identifier nobody recorded by hand.
4. **Creation, last, and only with a venue.** A security is created only
   when the share class is unanimous, the venue is one Atlas has measured,
   and that venue answers with exactly one listing.

Anything ambiguous withholds. The failure mode being designed against is not
"Atlas resolved nothing" -- it is "Atlas resolved Suncor Energy for a
Schneider Electric holding", which a ticker alone genuinely cannot prevent:
both are `SU`, and Suncor is a real row in this database. Their share
classes are `BBG001S5YSF0` and `BBG001S67MN2`, and no arrangement of those
two strings produces the other.

This resolver never fetches fundamentals and never decides anything about a
company. Knowing which security a holding is and having financial statements
for it are separate facts, and this one only establishes the first.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Protocol

from atlas.alpha.canonical_security.models import CanonicalSecurity, SecurityIdentifier
from atlas.alpha.canonical_security.value_objects import MicCode, SecurityType
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.service import (
    CanonicalSecurityResolutionService,
    ResolutionRequest,
)
from atlas.alpha.portfolio_import.isin import is_valid_isin, normalize_isin
from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiMatch,
    OpenFigiProviderUnavailable,
)
from atlas.alpha.security_identity_evidence.share_class_identity import share_class_identity
from atlas.alpha.security_identity_evidence.venues import mic_for_market, venue_for_mic

__all__ = [
    "PROVENANCE_BROKER_IMPORT",
    "PROVIDER_OPENFIGI",
    "ImportIdentityStatus",
    "ImportedIdentity",
    "ImportIdentityResolution",
    "resolve_imported_identity",
]

#: An ISIN that came from the investor's own brokerage file. OpenFIGI
#: consumes an ISIN and never returns one, so an identifier recorded with
#: this provenance could only have come from the import -- labelling it
#: `OPENFIGI` would claim corroboration that never happened.
PROVENANCE_BROKER_IMPORT = "BROKER_IMPORT"

#: The provider that answered the ISIN. Separate constant so the two never
#: get typed interchangeably at a call site.
PROVIDER_OPENFIGI = "OPENFIGI"

#: OpenFIGI's `securityType` -> Atlas's closed vocabulary. Exact strings
#: only; anything else becomes `OTHER`, which says "something exists here
#: and Atlas will not name its kind" rather than guessing `COMMON_STOCK`.
_SECURITY_TYPES: dict[str, SecurityType] = {
    "Common Stock": "COMMON_STOCK",
    "Depositary Receipt": "DEPOSITARY_RECEIPT",
    "ADR": "DEPOSITARY_RECEIPT",
    "ETP": "ETF",
}


class ImportIdentityStatus(str, Enum):
    """What one imported row's identity evidence established."""

    #: Strong identity matched a security Atlas already had. Nothing created.
    RESOLVED_EXISTING = "RESOLVED_EXISTING"
    #: Strong identity named a security Atlas did not have, and proved enough
    #: to create it.
    CONSTRUCTED = "CONSTRUCTED"
    #: Two identifiers pointed at different securities, or one identifier
    #: pointed at more than one. Never resolved by preferring one.
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    #: No valid ISIN, or a valid ISIN with no venue Atlas can act on. The row
    #: keeps whatever weaker handling it already had.
    INSUFFICIENT_IDENTITY = "INSUFFICIENT_IDENTITY"
    #: The provider was asked and honestly knew nothing. Distinct from a
    #: provider failure and from an ambiguity.
    NO_MATCH = "NO_MATCH"
    #: The network failed. Says nothing about the security; retrying is valid.
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"


@dataclass(frozen=True)
class ImportedIdentity:
    """The identity evidence one broker row carries, kept in separate
    fields on purpose.

    Collapsing these into a normalized ticker string is the shape of the
    original bug. In particular `account_currency` is held well away from
    anything about the security: it is the currency the investor's *account*
    reports in, and the live import recorded `SEK` against all 25 holdings
    including every American one. It can never become a listing currency,
    a venue or a country -- see `_candidate_from`, which does not read it.
    """

    ticker: str | None = None
    company_name: str | None = None
    #: As written in the file. Validated here, never trusted for being present.
    isin: str | None = None
    #: As written in the file, e.g. `Nasdaq Stockholm`.
    market: str | None = None
    #: Reporting currency of the account. Identity-inert by construction.
    account_currency: str | None = None
    instrument_type: str | None = None
    provenance: str = PROVENANCE_BROKER_IMPORT

    @property
    def valid_isin(self) -> str | None:
        """The ISIN only if it passes ISO 6166. A malformed identifier is
        not weak evidence, it is none: accepting it could match the wrong
        security, which is worse than matching nothing."""
        normalized = normalize_isin(self.isin)
        return normalized if is_valid_isin(normalized) else None

    @property
    def exchange_mic(self) -> MicCode | None:
        """The venue table answers in plain strings -- it sits outside the
        identity packages -- so the value object is built here."""
        mic = mic_for_market(self.market)
        return MicCode(mic) if mic is not None else None


@dataclass(frozen=True)
class ImportIdentityResolution:
    status: ImportIdentityStatus
    reason: str
    security: CanonicalSecurity | None = None
    #: Which identifier actually decided it -- `ISIN` when the master already
    #: had it, `SHARE_CLASS_FIGI` when the provider supplied it.
    strong_identifier_used: str | None = None
    share_class_figi: str | None = None
    venue_figi: str | None = None
    composite_figi: str | None = None
    exchange_mic: str | None = None
    #: Every provider call this resolution caused. Asserted by tests rather
    #: than assumed, since "resolution did not quietly fetch" is a claim.
    provider_calls: int = 0

    @property
    def resolved(self) -> bool:
        return self.status in (
            ImportIdentityStatus.RESOLVED_EXISTING,
            ImportIdentityStatus.CONSTRUCTED,
        )


class SecurityMasterReader(Protocol):
    def find_by_identifier(self, identifier_type: str, value: str) -> CanonicalSecurity | None: ...

    def find_by_ticker_and_exchange(self, ticker: str, exchange_mic: str) -> CanonicalSecurity | None: ...


MapIsinFn = Callable[[str], OpenFigiMappingResult]


def resolve_imported_identity(
    identity: ImportedIdentity,
    *,
    master: SecurityMasterReader,
    map_isin_fn: MapIsinFn,
    resolution_service: CanonicalSecurityResolutionService | None = None,
    clock: Any = None,
) -> ImportIdentityResolution:
    """Resolve one imported row to a canonical security, or refuse to.

    `map_isin_fn` is injected so the provider stays the caller's to own:
    tests pass a fake and assert the call count, and a row with no valid
    ISIN never reaches it at all.
    """
    isin = identity.valid_isin
    if isin is None:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.INSUFFICIENT_IDENTITY,
            reason=(
                "no valid ISIN on this row -- a ticker names a listing at one venue, "
                "not a security, and cannot create or match one here"
            ),
        )

    mic = identity.exchange_mic
    # What the row's *weak* evidence claims, resolved once. Not used to
    # identify anything -- only to notice that it names a different security
    # than the strong evidence does, which is the one disagreement that must
    # withhold rather than pick a side.
    rival = _security_named_by_ticker_and_venue(identity, mic, master)

    # 1. The master, by the exact identifier the investor supplied. No call.
    existing = master.find_by_identifier("ISIN", isin)
    if existing is not None:
        return _settle(
            existing, rival, mic, strong_identifier="ISIN", provider_calls=0,
            reason=f"ISIN {isin} is already recorded against this security",
        )

    # 2. The provider, for the one thing an ISIN unambiguously names.
    try:
        result = map_isin_fn(isin)
    except OpenFigiProviderUnavailable as error:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.PROVIDER_UNAVAILABLE,
            reason=f"identity provider unavailable: {str(error)[:160]}",
            provider_calls=1,
        )

    if not result.matches:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.NO_MATCH,
            reason=f"the identity provider recognised no security at ISIN {isin}",
            provider_calls=1,
        )

    # Rows carrying no share class are ignored rather than counted against
    # unanimity: 7 of Volvo B's 209 listings have none, and treating those
    # as disagreement would reject a completely unambiguous ISIN.
    share_classes = {m.share_class_figi for m in result.matches if m.share_class_figi}
    if not share_classes:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.NO_MATCH,
            reason=f"no listing of ISIN {isin} carried a share class to identify it by",
            provider_calls=1,
        )
    if len(share_classes) > 1:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.IDENTITY_CONFLICT,
            reason=(
                f"ISIN {isin} names {len(share_classes)} different share classes; "
                "it does not identify one security"
            ),
            provider_calls=1,
        )

    identified = share_class_identity(result.matches)
    assert identified is not None  # unanimity was just established
    figi = identified.share_class_figi

    # 3. The master again, now by the share class. This is how a security
    #    Atlas already knows is recognized from an ISIN nobody recorded.
    existing = master.find_by_identifier("SHARE_CLASS_FIGI", figi)
    if existing is not None:
        return _settle(
            existing, rival, mic, strong_identifier="SHARE_CLASS_FIGI", provider_calls=1,
            reason=f"share class {figi} is already recorded against this security",
            share_class_figi=figi,
        )

    # 4. Creation. A disagreement is checked before anything about venues:
    #    "these two identifiers name two securities" is a finding about this
    #    holding, while "Atlas cannot create at this venue" is a fact about
    #    Atlas. Reporting the second would hide the first.
    if rival is not None:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.IDENTITY_CONFLICT,
            reason=(
                f"ISIN {isin} names share class {figi}, but {identity.ticker!r} on "
                f"{mic.value if mic else '?'} is already {rival.canonical_company_name} "
                "-- two identifiers naming two securities, so neither is acted on"
            ),
            share_class_figi=figi,
            exchange_mic=mic.value if mic else None,
            provider_calls=1,
        )

    # Creation needs a venue, because a security without one is a ticker.
    venue = venue_for_mic(mic.value if mic is not None else None)
    if venue is None:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.INSUFFICIENT_IDENTITY,
            reason=(
                f"share class {figi} is not in the security master and the market "
                f"{identity.market!r} is not one Atlas can map to a venue, so there is "
                "no listing to create"
            ),
            share_class_figi=figi, provider_calls=1,
        )
    if not venue.openfigi_exchange_codes:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.INSUFFICIENT_IDENTITY,
            reason=(
                f"share class {figi} is not in the security master and Atlas has not "
                f"measured how the identity provider names {venue.mic}, so its listing "
                "cannot be selected"
            ),
            share_class_figi=figi, exchange_mic=venue.mic, provider_calls=1,
        )

    at_venue = [
        match for match in result.matches
        if match.share_class_figi == figi and match.exch_code in venue.openfigi_exchange_codes
    ]
    if not at_venue:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.NO_MATCH,
            reason=f"share class {figi} has no listing at {venue.mic}",
            share_class_figi=figi, exchange_mic=venue.mic, provider_calls=1,
        )
    venue_figis = {match.figi for match in at_venue}
    if len(venue_figis) > 1:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.IDENTITY_CONFLICT,
            reason=(
                f"share class {figi} has {len(venue_figis)} listings at {venue.mic}; "
                "which one this holding is cannot be proven"
            ),
            share_class_figi=figi, exchange_mic=venue.mic, provider_calls=1,
        )

    listing = at_venue[0]
    candidate = _candidate_from(identity, identified, listing, venue)
    service = resolution_service or CanonicalSecurityResolutionService()
    request = ResolutionRequest(
        investor_ticker=candidate.symbol,
        candidates=(candidate,),
        investor_company_text=identity.company_name,
    )
    outcome = service.resolve(request) if clock is None else service.resolve(request, clock=clock)
    if outcome.canonical_security is None:
        return ImportIdentityResolution(
            status=ImportIdentityStatus.INSUFFICIENT_IDENTITY,
            reason=(
                f"identity evidence for share class {figi} reached {outcome.outcome} "
                "rather than automatic acceptance"
            ),
            share_class_figi=figi, exchange_mic=venue.mic, provider_calls=1,
        )

    return ImportIdentityResolution(
        status=ImportIdentityStatus.CONSTRUCTED,
        reason=f"created from share class {figi} and its single listing at {venue.mic}",
        security=_with_identifiers(outcome.canonical_security, isin, figi, listing, outcome.resolved_at),
        strong_identifier_used="SHARE_CLASS_FIGI",
        share_class_figi=figi,
        venue_figi=listing.figi,
        composite_figi=listing.composite_figi,
        exchange_mic=venue.mic,
        provider_calls=1,
    )


def _with_identifiers(
    security: CanonicalSecurity,
    isin: str,
    share_class_figi: str,
    listing: OpenFigiMatch,
    recorded_at: datetime,
) -> CanonicalSecurity:
    """Record what identified this security, and who said so.

    The provenance split is the substantive part. OpenFIGI *consumes* an
    ISIN and never returns one, so the ISIN here can only have come from the
    investor's brokerage file -- labelling it `OPENFIGI` would claim a
    corroboration that never happened, and would make a single unverified
    source look like two agreeing ones. The three FIGIs did come from the
    provider, and are recorded as three separate types because they mean
    three different things: this listing, its composite, and the share class
    that is the same everywhere in the world.

    Recording them is also what makes a re-import cheap: the next file
    carrying this ISIN resolves out of the master with no provider call.
    """
    identifiers = [
        SecurityIdentifier(
            identifier_type="ISIN", value=isin, recorded_at=recorded_at,
            provider=PROVENANCE_BROKER_IMPORT, query_type="IMPORTED_ISIN", query_value=isin,
        ),
        SecurityIdentifier(
            identifier_type="SHARE_CLASS_FIGI", value=share_class_figi, recorded_at=recorded_at,
            provider=PROVIDER_OPENFIGI, query_type="ID_ISIN", query_value=isin,
            observed_at=recorded_at,
        ),
        SecurityIdentifier(
            identifier_type="FIGI", value=listing.figi, recorded_at=recorded_at,
            provider=PROVIDER_OPENFIGI, query_type="ID_ISIN", query_value=isin,
            observed_at=recorded_at,
        ),
    ]
    if listing.composite_figi:
        identifiers.append(SecurityIdentifier(
            identifier_type="COMPOSITE_FIGI", value=listing.composite_figi,
            recorded_at=recorded_at, provider=PROVIDER_OPENFIGI, query_type="ID_ISIN",
            query_value=isin, observed_at=recorded_at,
        ))
    for identifier in identifiers:
        security = security.add_identifier(identifier, clock=lambda: recorded_at)
    return security


def _security_named_by_ticker_and_venue(
    identity: ImportedIdentity, mic: MicCode | None, master: SecurityMasterReader
) -> CanonicalSecurity | None:
    """The security the row's ticker and venue name on their own, if any.

    This is weak evidence and is never allowed to identify anything. Its
    only job is to be compared against the strong answer, because the one
    situation that must withhold is two identifiers giving two different
    securities.
    """
    ticker = (identity.ticker or "").strip().upper()
    if not ticker or mic is None:
        return None
    return master.find_by_ticker_and_exchange(ticker, mic.value)


def _settle(
    existing: CanonicalSecurity,
    rival: CanonicalSecurity | None,
    mic: MicCode | None,
    *,
    strong_identifier: str,
    provider_calls: int,
    reason: str,
    share_class_figi: str | None = None,
) -> ImportIdentityResolution:
    """Accept the strong match, unless the weak evidence names a different
    security.

    A venue difference is deliberately not a conflict: a share class is the
    same share class in Stockholm and in Frankfurt, so a security matched by
    share class and imported from a second venue is a cross-listing, not a
    disagreement. A ticker that merely fails to corroborate is likewise
    ignored -- brokers spell tickers their own way (`VOLV-B` where the
    provider says `VOLVB`), and treating every spelling difference as a
    conflict would withhold on nearly every real row.
    """
    if rival is not None and str(rival.id) != str(existing.id):
        return ImportIdentityResolution(
            status=ImportIdentityStatus.IDENTITY_CONFLICT,
            reason=(
                f"{strong_identifier} names {existing.canonical_company_name}, but this "
                f"row's ticker and market name {rival.canonical_company_name}; Atlas has "
                "not linked this holding to either"
            ),
            share_class_figi=share_class_figi,
            exchange_mic=mic.value if mic else None,
            provider_calls=provider_calls,
        )
    return ImportIdentityResolution(
        status=ImportIdentityStatus.RESOLVED_EXISTING,
        reason=reason,
        security=existing,
        strong_identifier_used=strong_identifier,
        share_class_figi=share_class_figi,
        exchange_mic=mic.value if mic else None,
        provider_calls=provider_calls,
    )


def _candidate_from(
    identity: ImportedIdentity,
    identified: Any,
    listing: OpenFigiMatch,
    venue: Any,
) -> ProviderCandidate:
    """The provider's claim, as a candidate the normal resolution path can
    judge. `account_currency` is not read here and `currency` is left
    unset: OpenFIGI's mapping endpoint returns no currency field, so the
    only currency anywhere near this row is the account's, and borrowing it
    is precisely the error that recorded `SEK` against Microsoft."""
    return ProviderCandidate(
        provider_name="OPENFIGI",
        # The investor's own ticker where there is one: it is what the rest
        # of Atlas keys a holding on. The provider's own spelling is kept
        # beside it rather than silently replacing it.
        symbol=(identity.ticker or listing.ticker or "").strip().upper(),
        company_name=identified.name or listing.name,
        exchange_mic=MicCode(venue.mic),
        exchange_display_name=identity.market,
        country=venue.country,
        security_type=_SECURITY_TYPES.get(identified.security_type or "", "OTHER"),
        listing_relationship="NATIVE",
        figi=listing.figi,
        raw_metadata={
            "shareClassFIGI": identified.share_class_figi,
            "compositeFIGI": listing.composite_figi or "",
            "providerTicker": listing.ticker or "",
            "exchCode": listing.exch_code or "",
            "listingsAgreeing": str(identified.listing_count),
        },
    )
