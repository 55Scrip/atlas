"""Domain errors for the Conclusion aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations


class ConclusionError(Exception):
    """Base class for all Conclusion domain errors."""


class ConclusionValidationError(ConclusionError):
    """Raised when a Conclusion or one of its value objects fails an invariant."""


class MissingStatementError(ConclusionValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidConcludedAtError(ConclusionValidationError):
    """Raised when ConcludedAt is missing or not a timezone-aware datetime."""


class ConclusionNotFoundError(ConclusionError):
    """Raised when a requested Conclusion does not exist.

    Deliberately not a ConclusionValidationError: this is a missing
    reference, not a malformed value.
    """
