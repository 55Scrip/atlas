"""Domain errors for the Hypothesis aggregate (API-004 Hypothesis Capture)."""
from __future__ import annotations


class HypothesisError(Exception):
    """Base class for all Hypothesis domain errors."""


class HypothesisValidationError(HypothesisError):
    """Raised when a Hypothesis or one of its value objects fails an invariant."""


class MissingStatementError(HypothesisValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidFormulatedAtError(HypothesisValidationError):
    """Raised when FormulatedAt is missing or not a timezone-aware datetime."""


class HypothesisNotFoundError(HypothesisError):
    """Raised when a requested Hypothesis does not exist.

    Deliberately not a HypothesisValidationError: this is a missing
    reference, not a malformed value, and maps to 404 rather than 400.
    """
