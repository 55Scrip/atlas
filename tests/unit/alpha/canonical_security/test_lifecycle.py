"""Resolution lifecycle transition validation -- Sprint M Phase 5."""
from __future__ import annotations

import pytest

from atlas.alpha.canonical_security.exceptions import InvalidResolutionTransitionError
from atlas.alpha.canonical_security.lifecycle import is_legal_transition, is_terminal, validate_transition


@pytest.mark.parametrize(
    "current,requested",
    [
        ("DISCOVERED", "CANDIDATES_FOUND"),
        ("CANDIDATES_FOUND", "IDENTITY_VERIFIED"),
        ("CANDIDATES_FOUND", "REJECTED"),
        ("IDENTITY_VERIFIED", "CONFIRMED"),
        ("IDENTITY_VERIFIED", "REJECTED"),
        ("CONFIRMED", "CANONICAL"),
        ("CANONICAL", "ACTIVE"),
        ("ACTIVE", "SUPERSEDED"),
        ("ACTIVE", "MERGED"),
        ("ACTIVE", "REVOKED"),
        ("ACTIVE", "EXPIRED"),
    ],
)
def test_legal_transitions_accepted(current: str, requested: str) -> None:
    assert is_legal_transition(current, requested)  # type: ignore[arg-type]
    validate_transition(current, requested)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "current,requested",
    [
        ("DISCOVERED", "CANONICAL"),  # skip straight to canonical
        ("DISCOVERED", "ACTIVE"),
        ("CANDIDATES_FOUND", "CONFIRMED"),  # skip IDENTITY_VERIFIED
        ("CONFIRMED", "ACTIVE"),  # skip CANONICAL
        ("ACTIVE", "DISCOVERED"),  # reverse transition
        ("REJECTED", "CANDIDATES_FOUND"),  # out of a terminal state
        ("SUPERSEDED", "ACTIVE"),
        ("MERGED", "ACTIVE"),
        ("REVOKED", "ACTIVE"),
        ("EXPIRED", "ACTIVE"),
    ],
)
def test_illegal_transitions_rejected(current: str, requested: str) -> None:
    assert not is_legal_transition(current, requested)  # type: ignore[arg-type]
    with pytest.raises(InvalidResolutionTransitionError):
        validate_transition(current, requested)  # type: ignore[arg-type]


@pytest.mark.parametrize("status", ["REJECTED", "SUPERSEDED", "MERGED", "REVOKED", "EXPIRED"])
def test_terminal_statuses_have_no_outgoing_transitions(status: str) -> None:
    assert is_terminal(status)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "status",
    ["DISCOVERED", "CANDIDATES_FOUND", "IDENTITY_VERIFIED", "CONFIRMED", "CANONICAL", "ACTIVE"],
)
def test_non_terminal_statuses_have_outgoing_transitions(status: str) -> None:
    assert not is_terminal(status)  # type: ignore[arg-type]
