"""Domain errors for the DecisionContext aggregate (API-002 Decision Context)."""
from __future__ import annotations


class DecisionContextError(Exception):
    """Base class for all DecisionContext domain errors."""


class DecisionContextValidationError(DecisionContextError):
    """Raised when a DecisionContext or one of its value objects fails an invariant."""


class MissingSituationError(DecisionContextValidationError):
    """Raised when Situation is missing, or only whitespace."""


class InvalidAlternativeError(DecisionContextValidationError):
    """Raised when AlternativesConsidered contains an empty value."""


class InvalidUncertaintyError(DecisionContextValidationError):
    """Raised when Uncertainties contains an empty value."""


class InvalidCapturedAtError(DecisionContextValidationError):
    """Raised when CapturedAt is missing or not a timezone-aware datetime."""


class DecisionNotFoundError(DecisionContextError):
    """Raised when a DecisionContext is captured against a Decision that does not exist.

    Deliberately not a DecisionContextValidationError: this is a missing
    reference, not a malformed value, and maps to 404 rather than 400.
    """


class DuplicateDecisionContextError(DecisionContextError):
    """Raised when a Decision already has a DecisionContext.

    Each Decision may have at most one DecisionContext. Deliberately not a
    DecisionContextValidationError: this is a state conflict, and maps to
    409 rather than 400.
    """
