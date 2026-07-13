"""Domain errors for the Interpretation aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations


class InterpretationError(Exception):
    """Base class for all Interpretation domain errors."""


class InterpretationValidationError(InterpretationError):
    """Raised when an Interpretation or one of its value objects fails an invariant."""


class MissingStatementError(InterpretationValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidInterpretedAtError(InterpretationValidationError):
    """Raised when InterpretedAt is missing or not a timezone-aware datetime."""


class InterpretationNotFoundError(InterpretationError):
    """Raised when a requested Interpretation does not exist.

    Deliberately not an InterpretationValidationError: this is a missing
    reference, not a malformed value.
    """
