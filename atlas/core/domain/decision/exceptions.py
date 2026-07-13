"""Domain errors for the Decision aggregate (API-001 Decision Capture)."""
from __future__ import annotations


class DecisionError(Exception):
    """Base class for all Decision domain errors."""


class DecisionValidationError(DecisionError):
    """Raised when a Decision or one of its value objects fails an invariant."""


class MissingReasonError(DecisionValidationError):
    """Raised when an InvestmentCase has no reason, or only whitespace."""


class MissingSubjectError(DecisionValidationError):
    """Raised when a Subject is missing, or only whitespace.

    Every investment decision must be about something; Subject is a
    required aggregate invariant, not optional context.
    """


class InvalidDecisionTypeError(DecisionValidationError):
    """Raised when a DecisionType is not one of the allowed values."""


class MissingDecisionTypeError(InvalidDecisionTypeError):
    """Raised when no DecisionType was supplied at all."""


class InvalidConfidenceError(DecisionValidationError):
    """Raised when Confidence is missing, non-integer, or outside 0-100."""


class InvalidDecidedAtError(DecisionValidationError):
    """Raised when DecidedAt is missing or not a timezone-aware datetime."""
