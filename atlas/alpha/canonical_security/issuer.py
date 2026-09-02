"""`CanonicalIssuer` -- the legal/economic company Atlas analyses, as a
first-class concept separate from any tradeable instrument (Issuer
Identity Foundation, Phases 2, 7 and 8).

**Why this exists.** Until now a bare ticker string was the de-facto
primary key throughout Atlas, and `CanonicalSecurity` was a hybrid: an
issuer-shaped body (many listings, many provider mappings, many
identifiers) with security-level attributes welded onto its root. There
was no way to name Volvo AB without also asserting a ticker, an exchange
and a currency -- precisely the assertion that must not be made when the
only data available is a US OTC line for a Stockholm holding.

**Deliberately minimal.** `legal_name` and an optional `jurisdiction`,
plus identifiers. No ticker, no exchange, no trading currency, no share
class, no provider symbol -- each of those describes an *instrument*,
and putting any of them here would reintroduce the conflation this type
exists to remove. The temptation to add "primary ticker" for
convenience is exactly the mistake `CanonicalSecurity` already made.

**Lives inside `atlas.alpha.canonical_security`, not a new package.**
An issuer and its securities are one aggregate boundary and one
consistency domain, and this package is already the guarded identity
foundation that only its own tests, the Resolution Service and the
Identity Gate may import (see the integration-safety tests in this
package's own test directory). A sibling package would have needed a
second set of guard rules for no conceptual gain.

**What this module does NOT do.** It cannot merge issuers, resolve
cross-venue equivalence, or link `VOLV-B` to `VOLVF`. Those need strong
identifier evidence Atlas currently has none of -- zero identifier rows
exist in the live database -- and are explicitly out of scope. What is
here is the structure that makes such a link *expressible later* and
*refusable now*.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

from atlas.alpha.canonical_security.exceptions import (
    IssuerEquivalenceEvidenceTooWeakError,
)
from atlas.alpha.canonical_security.value_objects import (
    CanonicalIssuerId,
    IssuerIdentifierType,
    validate_issuer_identifier_type,
)

__all__ = [
    "CanonicalIssuer",
    "IssuerIdentifier",
    "IssuerEquivalenceEvidence",
    "STRONG_ISSUER_EVIDENCE",
    "WEAK_ISSUER_EVIDENCE",
    "may_link_to_existing_issuer",
    "require_strong_issuer_evidence",
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class IssuerIdentifier:
    """One regulatory/legal identifier for an issuer -- an LEI or an SEC
    CIK. Recorded opportunistically, exactly like `SecurityIdentifier`:
    never required for an issuer to exist, because no provider tier
    Atlas has tested returns one.

    An ISIN is deliberately *not* representable here. An ISIN names a
    security, and the whole point of this module is that the two layers
    do not share an identifier space."""

    identifier_type: IssuerIdentifierType
    value: str
    recorded_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        # Validated at runtime, not merely typed: a `Literal` is erased
        # at execution, and "ISIN" reaching this constructor is exactly
        # the layer confusion this module exists to prevent.
        validate_issuer_identifier_type(self.identifier_type)
        if not self.value or not self.value.strip():
            raise ValueError("IssuerIdentifier.value must not be blank")
        object.__setattr__(self, "value", self.value.strip().upper())


@dataclass(frozen=True)
class CanonicalIssuer:
    """The aggregate root for issuer identity. Frozen, like every other
    aggregate in this codebase -- `add_identifier` returns a new
    instance rather than mutating.

    `legal_name` is a *label*, never an identity key. Two issuers with
    identical names are still two issuers until a strong identifier says
    otherwise; see `may_link_to_existing_issuer` for why that rule is
    enforced in code rather than left to callers' judgement."""

    id: CanonicalIssuerId
    legal_name: str
    jurisdiction: str | None = None
    identifiers: tuple[IssuerIdentifier, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.legal_name or not self.legal_name.strip():
            raise ValueError("CanonicalIssuer.legal_name must not be blank")

    @classmethod
    def create(
        cls,
        *,
        legal_name: str,
        jurisdiction: str | None = None,
        clock=_utc_now,
    ) -> CanonicalIssuer:
        return cls(
            id=CanonicalIssuerId(),
            legal_name=legal_name.strip(),
            jurisdiction=jurisdiction,
            created_at=clock(),
        )

    def add_identifier(self, identifier: IssuerIdentifier) -> CanonicalIssuer:
        for existing in self.identifiers:
            if (
                existing.identifier_type == identifier.identifier_type
                and existing.value == identifier.value
            ):
                return self
        return replace(self, identifiers=self.identifiers + (identifier,))

    def identifier_of(self, identifier_type: IssuerIdentifierType) -> str | None:
        for identifier in self.identifiers:
            if identifier.identifier_type == identifier_type:
                return identifier.value
        return None


#: Evidence that may, on its own, justify linking a security to an
#: already-known issuer. Every member names a *registered identifier or
#: an official relationship*, never a resemblance.
STRONG_ISSUER_EVIDENCE: frozenset[str] = frozenset(
    {
        "LEI",
        "CIK",
        "EXPLICIT_ADR_UNDERLYING_MAPPING",
        "OFFICIAL_PROVIDER_ISSUER_ID",
        "USER_CONFIRMATION",
    }
)

#: Evidence that may never, in any combination, justify an automatic
#: link. This is the list the Volvo diagnostic made concrete: Alpha
#: Vantage returned `VOLVF` (Volvo AB) and `VLVOF` (**Volvo Car AB**)
#: tied at match score 0.8000. Ranking cannot separate two different
#: companies, so nothing derived from ranking or resemblance is allowed
#: to try.
WEAK_ISSUER_EVIDENCE: frozenset[str] = frozenset(
    {
        "COMPANY_NAME_SIMILARITY",
        "COMPANY_NAME_EXACT_MATCH",
        "TICKER_SIMILARITY",
        "EXCHANGE_MATCH",
        "COUNTRY_MATCH",
        "INDUSTRY_MATCH",
        "PROVIDER_MATCH_SCORE",
    }
)


@dataclass(frozen=True)
class IssuerEquivalenceEvidence:
    """What is known about a proposed "these two are the same company"
    claim. Deliberately a set of *named* evidence kinds rather than a
    numeric score: a score invites a threshold, and a threshold is
    exactly how `Volvo AB` and `Volvo Car AB` end up merged."""

    kinds: frozenset[str]

    @property
    def strong_kinds(self) -> frozenset[str]:
        return self.kinds & STRONG_ISSUER_EVIDENCE

    @property
    def has_strong_evidence(self) -> bool:
        return bool(self.strong_kinds)


def may_link_to_existing_issuer(evidence: IssuerEquivalenceEvidence) -> bool:
    """The one rule this sprint exists to make unbreakable: **no
    automatic issuer merge without strong evidence.**

    Note the asymmetry -- `COMPANY_NAME_EXACT_MATCH` is classified weak,
    not strong. An exact name match is still just a name, and the
    identity investigation showed name comparison failing in both
    directions at once: too strict to recognise `AB Volvo` as `Volvo AB`,
    too weak to keep `Volvo AB` apart from `Volvo Car AB` if loosened.
    Any threshold that fixes one failure worsens the other, so name is
    not permitted to decide this at any setting."""
    return evidence.has_strong_evidence


def require_strong_issuer_evidence(evidence: IssuerEquivalenceEvidence) -> None:
    """Raising counterpart, for call sites where silently declining to
    link would hide a real programming error."""
    if not may_link_to_existing_issuer(evidence):
        raise IssuerEquivalenceEvidenceTooWeakError(
            "Refusing to link a security to an existing issuer: evidence "
            f"{sorted(evidence.kinds)} contains no strong identifier. Strong evidence is "
            f"one of {sorted(STRONG_ISSUER_EVIDENCE)}. Name, ticker, exchange, country, "
            "industry and provider match scores are never sufficient alone."
        )
