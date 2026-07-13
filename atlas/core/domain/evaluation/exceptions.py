"""Domain errors for the Evaluation aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations


class EvaluationError(Exception):
    """Base class for all Evaluation domain errors."""


class EvaluationValidationError(EvaluationError):
    """Raised when an Evaluation or one of its value objects fails an invariant."""


class MissingStatementError(EvaluationValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidEvaluatedAtError(EvaluationValidationError):
    """Raised when EvaluatedAt is missing or not a timezone-aware datetime."""


class EvaluationNotFoundError(EvaluationError):
    """Raised when a requested Evaluation does not exist.

    Deliberately not an EvaluationValidationError: this is a missing
    reference, not a malformed value.
    """
