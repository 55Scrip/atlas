"""Domain errors for the Observation aggregate (API-003 Observation Capture)."""
from __future__ import annotations


class ObservationError(Exception):
    """Base class for all Observation domain errors."""


class ObservationValidationError(ObservationError):
    """Raised when an Observation or one of its value objects fails an invariant."""


class MissingSubjectError(ObservationValidationError):
    """Raised when Subject is missing, or only whitespace."""


class MissingStatementError(ObservationValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidObservedAtError(ObservationValidationError):
    """Raised when ObservedAt is missing or not a timezone-aware datetime."""
