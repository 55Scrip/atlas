"""Domain errors for the Outcome aggregate (ATLAS-001 Core Loop)."""
from __future__ import annotations


class OutcomeError(Exception):
    """Base class for all Outcome domain errors."""


class OutcomeValidationError(OutcomeError):
    """Raised when an Outcome or one of its value objects fails an invariant."""


class MissingStatementError(OutcomeValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidOccurredAtError(OutcomeValidationError):
    """Raised when OccurredAt is missing or not a timezone-aware datetime."""


class OutcomeNotFoundError(OutcomeError):
    """Raised when a requested Outcome does not exist.

    Deliberately not an OutcomeValidationError: this is a missing
    reference, not a malformed value.
    """


class DecisionNotFoundError(OutcomeError):
    """Raised when an Outcome is captured against a Decision that does not
    exist.

    Defined here, not imported, because Decision (API-001) has no
    NotFoundError of its own — the same situation decision_context
    (API-002) was in. This is an intentional, disclosed naming collision
    with decision_context.exceptions.DecisionNotFoundError, not a
    duplication oversight; see docs/CoreLoopATLAS001.md.
    """
