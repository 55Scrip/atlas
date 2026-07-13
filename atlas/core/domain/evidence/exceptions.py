"""Domain errors for the Evidence aggregate (API-005 Evidence Capture)."""
from __future__ import annotations


class EvidenceError(Exception):
    """Base class for all Evidence domain errors."""


class EvidenceValidationError(EvidenceError):
    """Raised when Evidence or one of its value objects fails an invariant."""


class MissingStatementError(EvidenceValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidDirectionError(EvidenceValidationError):
    """Raised when Direction is missing or not SUPPORTS/CHALLENGES."""


class InvalidObservedAtError(EvidenceValidationError):
    """Raised when ObservedAt is missing or not a timezone-aware datetime."""


class EvidenceNotFoundError(EvidenceError):
    """Raised when a requested Evidence record does not exist.

    Deliberately not an EvidenceValidationError: this is a missing
    reference, not a malformed value, and maps to 404 rather than 400.
    """
