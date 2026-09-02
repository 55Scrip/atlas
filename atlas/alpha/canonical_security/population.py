"""Deterministic `CanonicalSecurity` population planning.

**The problem this closes.** Whether a company has a `CanonicalSecurity`
currently depends on *when* it was ingested, not on what Atlas knows
about it. 14 of 36 companies have one; the rest entered before the
Identity Gate existed and have carried authoritative evidence ever since
without anything acting on it. Identity must not depend on historical
accident.

**Planning only. This module has no side effects at all** -- no
repository, no database, no provider. It reads evidence a caller has
already gathered and returns what *would* happen. Creation stays with
the Identity Gate, which is the only component allowed to mint identity.

**What the audit established.** Issuer identity alone cannot create a
security. A CIK proves which filer a company is; it says nothing about
which exchange the instrument trades on or in what currency, and
`CanonicalSecurity` requires both. Those live only in a company-profile
document. So the answer to "can a proven issuer produce a security?" is
**no** -- but "can *stored* evidence produce one?" is yes for every
company whose profile document was captured before the gate existed.

**On the one association this module does make.** A profile document is
matched to its company by the `company` field the provider's own fetch
stamped on it -- the same association the original request made. That is
provenance, not inference: Atlas is not deciding that some document
*probably* describes this company, it is reading a document that was
retrieved *for* this company. No comparison is ever made across
companies, so nothing here can turn `SU.PA` into Suncor.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "PopulationOutcome",
    "SecurityPopulationPlan",
    "REQUIRED_PROFILE_FIELDS",
    "plan_security_population",
]

#: The fields a stored profile document must carry before a
#: `CanonicalSecurity` can be constructed from it. Derived from
#: `CanonicalSecurity.discover`'s own required arguments, not chosen
#: independently -- `country` is included because `discover` requires it.
#:
#: `asset_type` is deliberately absent: `SecurityType` already degrades
#: to `OTHER` when a provider omits it, so requiring it would block
#: creation over a field the model itself treats as optional.
REQUIRED_PROFILE_FIELDS: tuple[str, ...] = ("name", "exchange", "currency", "country")


class PopulationOutcome(str, Enum):
    """Why one company does or does not have a `CanonicalSecurity`, and
    what it would take to give it one."""

    #: A security already exists. Nothing to do.
    ALREADY_PRESENT = "already_present"
    #: A stored profile document carries everything needed. The Identity
    #: Gate can be replayed against evidence already held -- **no
    #: provider call**.
    READY_TO_CREATE = "ready_to_create"
    #: No stored profile document, or one missing required fields. Only
    #: a live profile fetch can supply exchange and currency.
    REQUIRES_PROVIDER_CALL = "requires_provider_call"
    #: Stored profiles disagree about identity. Atlas does not choose.
    CONTRADICTORY = "contradictory"
    #: No evidence of any kind for this company.
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class SecurityPopulationPlan:
    company: str
    outcome: PopulationOutcome
    reason: str
    missing_fields: tuple[str, ...] = ()
    #: Present only for `READY_TO_CREATE` -- the exact profile metadata
    #: a caller would hand to the gate, so the plan is auditable rather
    #: than merely a verdict.
    profile: dict | None = None

    @property
    def needs_provider_call(self) -> bool:
        return self.outcome is PopulationOutcome.REQUIRES_PROVIDER_CALL

    @property
    def is_actionable_offline(self) -> bool:
        return self.outcome is PopulationOutcome.READY_TO_CREATE


#: Fields whose *disagreement* means two profiles describe different
#: things. Absence is never disagreement -- see `_contradicts`.
_IDENTITY_FIELDS: tuple[str, ...] = ("name", "exchange", "currency")


def _value(profile: dict, field: str) -> str | None:
    raw = profile.get(field)
    text = str(raw).strip().casefold() if raw is not None else ""
    return text or None


def _contradicts(profiles: tuple[dict, ...]) -> bool:
    """Two profiles contradict only where both state a value and the
    values differ.

    A field one profile omits is silence, not disagreement -- an earlier
    refresh that captured no `currency` does not contradict a later one
    that did. Treating absence as conflict would be the same
    absence-means-disagreement error this codebase has already had to
    remove twice (an empty provider payload read as "no identity", a
    missing CIK read as a different filer)."""
    for field in _IDENTITY_FIELDS:
        stated = {value for profile in profiles if (value := _value(profile, field)) is not None}
        if len(stated) > 1:
            return True
    return False


def plan_security_population(
    company: str,
    *,
    has_security: bool,
    profiles: tuple[dict, ...],
) -> SecurityPopulationPlan:
    """Pure and deterministic. `profiles` is the metadata of every stored
    `company_profile` document for this company, newest last.

    A company with several profile documents is normal -- each refresh
    stores one. They are treated as contradictory only if they disagree
    about *identity* (name, exchange, currency); differing on an
    optional field like `asset_type` is ordinary provider variation and
    the most complete profile is used.
    """
    if has_security:
        return SecurityPopulationPlan(
            company=company,
            outcome=PopulationOutcome.ALREADY_PRESENT,
            reason="A CanonicalSecurity already exists for this company.",
        )

    if not profiles:
        return SecurityPopulationPlan(
            company=company,
            outcome=PopulationOutcome.REQUIRES_PROVIDER_CALL,
            reason=(
                "No company-profile document is stored. Exchange and trading currency exist only "
                "in a profile, and neither can be derived from filings or a CIK, so identity "
                "cannot be established without one live profile fetch."
            ),
            missing_fields=REQUIRED_PROFILE_FIELDS,
        )

    if _contradicts(profiles):
        return SecurityPopulationPlan(
            company=company,
            outcome=PopulationOutcome.CONTRADICTORY,
            reason=(
                "Stored profile documents disagree about name, exchange or currency. Atlas does "
                "not choose between them."
            ),
        )

    # Prefer the profile carrying the most required fields; ties resolve
    # to the last stored, which is the most recent refresh.
    best = max(
        profiles,
        key=lambda profile: sum(1 for field in REQUIRED_PROFILE_FIELDS if profile.get(field)),
    )
    missing = tuple(field for field in REQUIRED_PROFILE_FIELDS if not best.get(field))
    if missing:
        return SecurityPopulationPlan(
            company=company,
            outcome=PopulationOutcome.REQUIRES_PROVIDER_CALL,
            reason=(
                "A profile document is stored but does not carry every field CanonicalSecurity "
                f"requires (missing: {', '.join(missing)}). A fresh profile fetch is needed."
            ),
            missing_fields=missing,
        )

    return SecurityPopulationPlan(
        company=company,
        outcome=PopulationOutcome.READY_TO_CREATE,
        reason=(
            "A stored profile document carries every field required. The Identity Gate can be "
            "replayed against evidence Atlas already holds, with no provider call."
        ),
        profile=dict(best),
    )
