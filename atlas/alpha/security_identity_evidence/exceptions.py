"""Domain errors for Security Identity Evidence. Kept separate from
`security_confirmation`'s own errors -- this package's failures are
about verification, never about confirmation validity itself."""
from __future__ import annotations


class SecurityIdentityEvidenceError(Exception):
    """Base class for this package's own errors."""


class NoActiveConfirmationError(SecurityIdentityEvidenceError):
    """Raised when a Decision has no current confirmed selection to
    verify -- there is nothing for external evidence to be about.
    Maps to 404. Deliberately a distinct class from
    `security_confirmation.exceptions.NoActiveConfirmationError`
    rather than importing that one -- the two packages' failures are
    conceptually different even though the English message is similar
    (mirrors `security_confirmation.exceptions.SecurityConfirmationError`
    being its own base rather than reusing Core's)."""

    def __init__(self, decision_id: str) -> None:
        self.decision_id = decision_id
        super().__init__(f"Decision {decision_id} has no current confirmed security selection to verify")
