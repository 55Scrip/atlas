"""Domain errors for the Learning aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations


class LearningError(Exception):
    """Base class for all Learning domain errors."""


class LearningValidationError(LearningError):
    """Raised when a Learning or one of its value objects fails an invariant."""


class MissingStatementError(LearningValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidLearnedAtError(LearningValidationError):
    """Raised when LearnedAt is missing or not a timezone-aware datetime."""


class LearningNotFoundError(LearningError):
    """Raised when a requested Learning does not exist.

    Deliberately not a LearningValidationError: this is a missing
    reference, not a malformed value. Defined for symmetry with the
    other nine Core Loop steps even though Learning is the terminal
    node — nothing downstream reuses it.
    """
