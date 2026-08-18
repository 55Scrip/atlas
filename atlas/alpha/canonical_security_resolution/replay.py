"""Replay Engine -- Sprint N Phase 12.

Given a `StoredResolution` (loaded from `repository.py`), reconstructs
the exact `ResolutionRequest` that produced it and re-runs `resolve()`
under the same algorithm version. Because `resolve()` is built entirely
from pure functions plus one injectable `clock` (`service.py`'s own
docstring), replaying with `clock` pinned to the originally-recorded
`resolved_at` must produce byte-for-byte the same outcome, confidences,
and selected candidate -- if it doesn't, that is a real determinism bug
in the resolution algorithm, not a data problem, and `verify_replay`
raises `ReplayMismatchError` naming exactly which field diverged rather
than silently accepting a different answer.

Replay is only meaningful within one algorithm version
(`RESOLUTION_ALGORITHM_VERSION`, `service.py`) -- see
`ReplayVersionMismatchError`'s own docstring for why a version mismatch
is never treated as a determinism failure.
"""
from __future__ import annotations

from typing import Callable

from atlas.alpha.canonical_security.models import CanonicalSecurity
from atlas.alpha.canonical_security_resolution.exceptions import ReplayMismatchError, ReplayVersionMismatchError
from atlas.alpha.canonical_security_resolution.repository import StoredResolution
from atlas.alpha.canonical_security_resolution.service import (
    RESOLUTION_ALGORITHM_VERSION,
    CanonicalSecurityResolutionService,
    ResolutionRequest,
    ResolutionResult,
)

ExistingSecurityLookup = Callable[[str], "CanonicalSecurity | None"]


def replay(stored: StoredResolution, *, existing_lookup: ExistingSecurityLookup | None = None) -> ResolutionResult:
    """Re-runs the resolution algorithm against `stored`'s evidence.
    Does not itself assert anything about the result -- see
    `verify_replay` for the assertion-checking counterpart. Kept
    separate so a caller who only wants to inspect a fresh
    `ResolutionResult` (e.g. for display) isn't forced to also handle
    `ReplayMismatchError`."""
    if stored.resolution_version != RESOLUTION_ALGORITHM_VERSION:
        raise ReplayVersionMismatchError(stored.resolution_version, RESOLUTION_ALGORITHM_VERSION)

    existing: CanonicalSecurity | None = None
    if stored.existing_canonical_security_id is not None and existing_lookup is not None:
        existing = existing_lookup(stored.existing_canonical_security_id)

    request = ResolutionRequest(
        investor_ticker=stored.investor_ticker,
        candidates=tuple(item.candidate for item in stored.evidence),
        investor_company_text=stored.investor_company_text,
        existing_canonical_security=existing,
    )
    service = CanonicalSecurityResolutionService()
    return service.resolve(request, clock=lambda: stored.resolved_at)


def verify_replay(
    stored: StoredResolution, *, existing_lookup: ExistingSecurityLookup | None = None
) -> ResolutionResult:
    """Replays `stored` and asserts the guarantee this whole mechanism
    exists to prove: same evidence -> same outcome -> same confidence
    -> same selected candidate. Raises `ReplayMismatchError` naming the
    first field that diverges; returns the freshly replayed
    `ResolutionResult` when everything matches."""
    replayed = replay(stored, existing_lookup=existing_lookup)

    if replayed.outcome != stored.outcome:
        raise ReplayMismatchError("outcome", stored.outcome, replayed.outcome)

    stored_confidences = tuple(item.confidence for item in stored.evidence)
    replayed_confidences = tuple(item.confidence for item in replayed.evidence)
    if replayed_confidences != stored_confidences:
        raise ReplayMismatchError("confidences", stored_confidences, replayed_confidences)

    stored_selected_symbol = next((item.candidate.symbol for item in stored.evidence if item.accepted), None)
    replayed_selected_symbol = replayed.selected_candidate.symbol if replayed.selected_candidate else None
    if replayed_selected_symbol != stored_selected_symbol:
        raise ReplayMismatchError("selected_candidate", stored_selected_symbol, replayed_selected_symbol)

    return replayed
