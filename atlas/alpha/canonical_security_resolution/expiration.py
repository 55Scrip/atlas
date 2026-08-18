"""Resolution Expiration -- Sprint N Phase 13.

Pure, deterministic domain logic only -- no scheduler, no background
job, nothing that runs on a timer. Every function here is computed
on-read, the moment a caller asks "is this still trustworthy," using
whatever `now` the caller supplies (never a bare `datetime.now()` call
buried inside these functions, so tests remain fully deterministic and
no hidden wall-clock dependency exists anywhere in this module).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from atlas.alpha.canonical_security.value_objects import IdentityConfidence

#: Default staleness window -- a resolution older than this is no longer
#: treated as fresh evidence. Deliberately conservative (aligned with
#: how long a company's exchange listing or corporate identity
#: realistically stays stable) rather than tuned against any real
#: production data, since none exists yet for this shadow-mode service.
DEFAULT_MAX_AGE = timedelta(days=180)

_TIER_ORDER: tuple[IdentityConfidence, ...] = ("LOW", "MEDIUM", "HIGH")


def is_resolution_expired(resolved_at: datetime, *, now: datetime, max_age: timedelta = DEFAULT_MAX_AGE) -> bool:
    return (now - resolved_at) > max_age


def requires_revalidation(resolved_at: datetime, *, now: datetime, max_age: timedelta = DEFAULT_MAX_AGE) -> bool:
    """Identical to `is_resolution_expired` today -- kept as a distinct
    function because the two concepts are not guaranteed to stay
    identical forever (a future policy might require revalidation
    earlier than outright expiration, e.g. to prompt a lighter-weight
    re-check before a resolution is fully discarded). Callers should
    use whichever name matches their actual question, not assume the
    two will always agree."""
    return is_resolution_expired(resolved_at, now=now, max_age=max_age)


def age_confidence(
    confidence: IdentityConfidence, *, resolved_at: datetime, now: datetime, max_age: timedelta = DEFAULT_MAX_AGE
) -> IdentityConfidence:
    """Confidence aging: a resolution past `max_age` has its confidence
    downgraded by one tier (`HIGH` -> `MEDIUM`, `MEDIUM` -> `LOW`) --
    never upgraded, and `LOW`/`REJECTED` are left as-is (there is no
    tier below them to downgrade to). This is a pure, deterministic
    function of `(confidence, resolved_at, now)` -- calling it twice
    with the same inputs always returns the same result, with no
    persistent side effect and no background process required to keep
    it accurate; staleness is simply a function of how far `now` has
    moved past `resolved_at` at the moment of the call."""
    if confidence == "REJECTED":
        return confidence
    if not is_resolution_expired(resolved_at, now=now, max_age=max_age):
        return confidence
    if confidence not in _TIER_ORDER:
        return confidence
    index = _TIER_ORDER.index(confidence)
    return _TIER_ORDER[max(index - 1, 0)]
