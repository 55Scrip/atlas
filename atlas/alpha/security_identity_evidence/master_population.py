"""Give each canonical security the identifiers that survive a venue change.

Atlas's security master carries tickers and MICs and nothing stronger: zero
ISINs, zero FIGIs, for all 37 securities. That is survivable only while every
security is American and every provider speaks American tickers. It stops
working the moment an investor imports a holding from Stockholm -- and it is
actively unsafe where a ticker is reused, which is not rare: Schneider
Electric trades as `SU` in Paris and Suncor Energy trades as `SU` in Canada.

This asks OpenFIGI what a security *is*, by the pair Atlas already knows to
be safe -- ticker together with venue, never ticker alone -- and records the
three FIGIs it returns as separate identifier types, because they mean three
different things.

Nothing here decides anything about a company. A FIGI is a name, not a fact
about earnings, and populating one must never change a Case.

Refusals, all of them deliberate:

* A security with no venue is skipped. Asking OpenFIGI for a bare ticker is
  the exact question that cannot distinguish Schneider from Suncor.
* A response that does not name one share class unanimously writes nothing.
* An identifier already recorded with a different value is a conflict, not
  an update. Someone must look at it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiProviderUnavailable,
)
from atlas.alpha.security_identity_evidence.share_class_identity import share_class_identity

__all__ = [
    "PROVIDER",
    "SecurityIdentityPlan",
    "PopulationOutcome",
    "exchange_code_for_mic",
    "plan_identity",
]

PROVIDER = "OPENFIGI"

#: MIC -> OpenFIGI exchange code. OpenFIGI does not speak MICs; it has its
#: own short codes, and `US` is the composite covering both American venues
#: (verified live: `TICKER MSFT` + `exchCode US` returns exactly one match).
#: A closed table of pairs actually verified, never a derivation -- an
#: unlisted MIC yields `None` and that security is simply not queried, which
#: is the safe outcome rather than a guess at a venue.
_MIC_TO_EXCHANGE_CODE: dict[str, str] = {
    "XNAS": "US",
    "XNYS": "US",
}


def exchange_code_for_mic(mic: str | None) -> str | None:
    if mic is None:
        return None
    return _MIC_TO_EXCHANGE_CODE.get(mic.strip().upper())


@dataclass(frozen=True)
class SecurityIdentityPlan:
    """What one security would gain, and why it might gain nothing."""

    ticker: str
    mic: str | None
    exchange_code: str | None
    eligible: bool
    reason: str
    figi: str | None = None
    composite_figi: str | None = None
    share_class_figi: str | None = None
    provider_name: str | None = None
    listing_count: int = 0


@dataclass(frozen=True)
class PopulationOutcome:
    planned: tuple[SecurityIdentityPlan, ...] = field(default_factory=tuple)

    @property
    def eligible(self) -> tuple[SecurityIdentityPlan, ...]:
        return tuple(plan for plan in self.planned if plan.eligible)

    @property
    def resolved(self) -> tuple[SecurityIdentityPlan, ...]:
        return tuple(plan for plan in self.planned if plan.share_class_figi is not None)


def plan_identity(
    *,
    ticker: str,
    mic: str | None,
    lookup,
) -> SecurityIdentityPlan:
    """Ask the provider about one security, and interpret the answer.

    `lookup(ticker, exchange_code) -> OpenFigiMappingResult` is injected so
    this stays a pure decision about what an answer means; the caller owns
    the network, the pacing and the budget.
    """
    exchange_code = exchange_code_for_mic(mic)
    if mic is None:
        return SecurityIdentityPlan(
            ticker=ticker, mic=mic, exchange_code=None, eligible=False,
            reason="no venue recorded -- a bare ticker cannot identify a security")
    if exchange_code is None:
        return SecurityIdentityPlan(
            ticker=ticker, mic=mic, exchange_code=None, eligible=False,
            reason=f"no verified OpenFIGI exchange code for {mic}")

    try:
        result: OpenFigiMappingResult = lookup(ticker, exchange_code)
    except OpenFigiProviderUnavailable as error:
        return SecurityIdentityPlan(
            ticker=ticker, mic=mic, exchange_code=exchange_code, eligible=True,
            reason=f"provider unavailable: {str(error)[:120]}")

    if not result.matches:
        return SecurityIdentityPlan(
            ticker=ticker, mic=mic, exchange_code=exchange_code, eligible=True,
            reason="provider recognised no security at this ticker and venue")

    identity = share_class_identity(result.matches)
    if identity is None:
        return SecurityIdentityPlan(
            ticker=ticker, mic=mic, exchange_code=exchange_code, eligible=True,
            reason="listings did not agree on one share class")

    # The venue-level FIGI is only meaningful when the venue answered once.
    venue_figis = {m.figi for m in result.matches}
    composites = {m.composite_figi for m in result.matches if m.composite_figi}
    return SecurityIdentityPlan(
        ticker=ticker, mic=mic, exchange_code=exchange_code, eligible=True,
        reason="resolved",
        figi=venue_figis.pop() if len(venue_figis) == 1 else None,
        composite_figi=composites.pop() if len(composites) == 1 else None,
        share_class_figi=identity.share_class_figi,
        provider_name=identity.name,
        listing_count=identity.listing_count,
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
