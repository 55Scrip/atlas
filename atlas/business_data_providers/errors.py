"""Provider error taxonomy (ATLAS-031, Phase 13).

Every real fetch failure raises one of these -- never silently
converted into an empty, successful `()` return. Distinguishing "we
checked and the data genuinely doesn't exist" (a normal, honest
`RawBusinessDocument` gap the pipeline reports through
`ValidationRejection`/missing-fact handling) from "the provider call
itself failed" (a network/operational problem) is the whole point of
this module -- callers (`refresh_company_data`) catch these, record
them in a `RefreshSummary.provider_errors` entry, and never translate
one into the other.

`StaleMarketData` and `PartialHistoricalCoverage` are deliberately
**not** exceptions here: staleness is already a real, tested downstream
concern (`valuation.cash_flow`'s own `STALE_MARKET_DATA` gap), and
partial historical coverage is an honest, non-exceptional shape of a
successful fetch (fewer documents than hoped, not a failure) -- raising
for either would contradict Phase 13's own "do not convert missing data
into a failure" half of the same instruction.
"""
from __future__ import annotations

__all__ = [
    "BusinessDataProviderError",
    "CompanyNotFound",
    "AmbiguousSymbol",
    "ProviderUnavailable",
    "ProviderTimeout",
    "MalformedProviderResponse",
    "MissingRequiredField",
    "UnsupportedUnit",
    "RateLimited",
    "DailyQuotaExhausted",
]


class BusinessDataProviderError(Exception):
    """Base for every real-provider fetch failure. Never raised
    directly -- always one of the specific subclasses below."""


class CompanyNotFound(BusinessDataProviderError):
    """The provider has no record for this company identifier at all --
    a real, checked absence, not a guess."""


class AmbiguousSymbol(BusinessDataProviderError):
    """The company identifier resolves to more than one candidate and
    this provider's v1 identity resolution refuses to guess which one
    is meant (Phase 5: "fail explicitly, do not guess")."""


class ProviderUnavailable(BusinessDataProviderError):
    """The provider's service itself failed (5xx, connection refused,
    DNS failure) -- distinct from the company simply not existing."""


class ProviderTimeout(BusinessDataProviderError):
    """The request did not complete within the bounded timeout."""


class MalformedProviderResponse(BusinessDataProviderError):
    """The provider returned a 2xx response this code cannot parse into
    the shape it documents -- a real, observable provider-contract
    break, never silently coerced into a partial result."""


class MissingRequiredField(BusinessDataProviderError):
    """The provider's response parsed successfully but is missing a
    field this provider's v1 contract requires to construct even one
    `RawBusinessDocument` (e.g. no CIK resolvable, no price field
    present at all)."""


class UnsupportedUnit(BusinessDataProviderError):
    """The provider reports a currency/unit this provider's v1 does not
    support combining with the rest of the fetch (Phase 26: prefer an
    honest unsupported state over silently mixing units)."""


class RateLimited(BusinessDataProviderError):
    """The provider explicitly signaled a rate limit -- distinguished
    from a generic `ProviderUnavailable` so a caller can decide to
    retry later specifically because of quota, not because the service
    is down.

    **This base class now means specifically a SHORT-TERM limit** -- a
    pacing/burst rejection a caller may retry within seconds. A
    provider's *daily* allowance being spent is the `DailyQuotaExhausted`
    subclass below. Kept as the base (rather than becoming a sibling)
    so every existing `except RateLimited` and every existing
    `kind == "RateLimited"` classification keeps catching both cases
    exactly as before -- the split adds precision without changing what
    any current handler catches."""


class DailyQuotaExhausted(RateLimited):
    """The provider confirmed its *daily* allowance is spent (Provider &
    Quota Intelligence sprint).

    Separated from short-term pacing because the two demand wildly
    different waits -- roughly one second versus up to a full reset
    cycle -- and collapsing them is what let one throttled run spend 16
    consecutive calls, each rejected, each learning nothing new.

    Alpha Vantage signals both through the same `Information` key, so
    only the message text distinguishes them; see
    `alpha_vantage._check_for_provider_error` for the exact, observed
    strings this is matched on. **The reset boundary is deliberately not
    encoded here**: Alpha Vantage does not publish when the daily
    allowance resets (verified against its own support and premium
    pages), so any constant would be a guess. Deciding when to retry is
    the caller's job, from persisted provider state."""
