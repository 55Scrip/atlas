"""The Canonical Security resolution lifecycle -- Sprint L Phase 6's
state diagram, implemented as an explicit legal-transition table plus
one pure function that checks a requested transition against it.

Kept as its own module, separate from `models.py`, so the transition
rules are reviewable and testable independent of the aggregate's other
invariants (e.g. the CANONICAL/ACTIVE listing requirement, which is
enforced separately in `models.py` since it depends on aggregate state
this table has no access to).

Every state's outgoing edges below match the diagram in
`docs/canonical_security_foundation_implementation_design.md` Phase 6,
plus `EXPIRED` (Sprint M's own addition -- Sprint L's "identity expires"
remaining unknown, reachable only from `ACTIVE`). `REJECTED`,
`SUPERSEDED`, `MERGED`, `REVOKED`, and `EXPIRED` are terminal: none of
them appear as a key below, so any transition requested *from* one of
them is rejected by `is_legal_transition` returning `False` for an
unknown current status, and by `validate_transition` raising.
"""
from __future__ import annotations

from atlas.alpha.canonical_security.exceptions import InvalidResolutionTransitionError
from atlas.alpha.canonical_security.value_objects import ResolutionStatus

_LEGAL_TRANSITIONS: dict[ResolutionStatus, frozenset[ResolutionStatus]] = {
    "DISCOVERED": frozenset({"CANDIDATES_FOUND"}),
    "CANDIDATES_FOUND": frozenset({"IDENTITY_VERIFIED", "REJECTED"}),
    "IDENTITY_VERIFIED": frozenset({"CONFIRMED", "REJECTED"}),
    "CONFIRMED": frozenset({"CANONICAL"}),
    "CANONICAL": frozenset({"ACTIVE"}),
    "ACTIVE": frozenset({"SUPERSEDED", "MERGED", "REVOKED", "EXPIRED"}),
    # REJECTED, SUPERSEDED, MERGED, REVOKED, EXPIRED are terminal --
    # deliberately absent as keys, so any transition requested from one
    # of them is rejected below.
}


def is_legal_transition(current: ResolutionStatus, requested: ResolutionStatus) -> bool:
    return requested in _LEGAL_TRANSITIONS.get(current, frozenset())


def validate_transition(current: ResolutionStatus, requested: ResolutionStatus) -> None:
    if not is_legal_transition(current, requested):
        raise InvalidResolutionTransitionError(current, requested)


def is_terminal(status: ResolutionStatus) -> bool:
    """A terminal status has no legal outgoing transitions at all."""
    return status not in _LEGAL_TRANSITIONS
