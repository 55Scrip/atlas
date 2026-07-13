"""Domain errors for the Question aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations


class QuestionError(Exception):
    """Base class for all Question domain errors."""


class QuestionValidationError(QuestionError):
    """Raised when a Question or one of its value objects fails an invariant."""


class MissingStatementError(QuestionValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidRaisedAtError(QuestionValidationError):
    """Raised when RaisedAt is missing or not a timezone-aware datetime."""


class QuestionNotFoundError(QuestionError):
    """Raised when a requested Question does not exist.

    Deliberately not a QuestionValidationError: this is a missing
    reference, not a malformed value.
    """
