"""Domain errors for Security Confirmation. Kept separate from Core's
`DecisionValidationError` -- this package's failures are about
confirmation semantics, never about Decision validity itself."""
from __future__ import annotations


class SecurityConfirmationError(Exception):
    """Base class for this package's own errors."""


class DecisionNotFoundError(SecurityConfirmationError):
    """Raised when `decision_id` does not name a real, existing
    Decision. Maps to 404 -- see `api/errors.py`."""

    def __init__(self, decision_id: str) -> None:
        self.decision_id = decision_id
        super().__init__(f"Decision {decision_id!r} not found")


class UnsupportedDiscoverySourceError(SecurityConfirmationError):
    """Raised when `discovery_source` names something other than a
    source this package actually knows how to attribute provenance to
    -- a minimal guard against silently inventing a new source rather
    than an attempt to validate that discovery genuinely produced this
    exact candidate (which this package cannot verify at all; see
    `__init__.py`). Maps to 422."""

    def __init__(self, discovery_source: str) -> None:
        self.discovery_source = discovery_source
        super().__init__(f"Unsupported discovery source: {discovery_source!r}")


class ConflictingConfirmationError(SecurityConfirmationError):
    """Raised when a Decision already carries a confirmation for a
    *different* ticker. Never silently overwritten (Sprint 20 ground
    rule: "must not silently replace anything") -- maps to 409. A
    resubmission of the *same* ticker is idempotent and never reaches
    this error; see `service.py`."""

    def __init__(self, decision_id: str, existing_ticker: str, requested_ticker: str) -> None:
        self.decision_id = decision_id
        self.existing_ticker = existing_ticker
        self.requested_ticker = requested_ticker
        super().__init__(
            f"Decision {decision_id} already has a confirmed security selection "
            f"({existing_ticker!r}); refusing to silently replace it with {requested_ticker!r}."
        )
