"""Domain errors for the Evidence aggregate (API-005 Evidence Capture)."""
from __future__ import annotations


class EvidenceError(Exception):
    """Base class for all Evidence domain errors."""


class EvidenceValidationError(EvidenceError):
    """Raised when Evidence or one of its value objects fails an invariant."""


class MissingStatementError(EvidenceValidationError):
    """Raised when Statement is missing, or only whitespace."""


class InvalidDirectionError(EvidenceValidationError):
    """Raised when Direction is missing or not SUPPORTS/CHALLENGES."""


class InvalidObservedAtError(EvidenceValidationError):
    """Raised when ObservedAt is missing or not a timezone-aware datetime."""


class EvidenceNotFoundError(EvidenceError):
    """Raised when a requested Evidence record does not exist.

    Deliberately not an EvidenceValidationError: this is a missing
    reference, not a malformed value, and maps to 404 rather than 400.
    """


class ObservationNotFoundError(EvidenceError):
    """Raised when Evidence is captured against an Observation that does
    not exist.

    Defined here, not imported from Observation (API-003 has no
    NotFoundError of its own) — the same situation DecisionContext
    (API-002) was in with respect to Decision, and the same placement
    convention: the referencing aggregate's own exceptions module, not
    the referenced one's. Deliberately not an EvidenceValidationError:
    this is a missing reference, not a malformed value, and maps to 404
    rather than 400.
    """
