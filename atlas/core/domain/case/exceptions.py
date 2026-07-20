"""Domain errors for the Case aggregate (DO-IMP-001 Case Aggregate)."""
from __future__ import annotations


class CaseError(Exception):
    """Base class for all Case domain errors."""


class CaseNotFoundError(CaseError):
    """Raised when a requested Case does not exist.

    Case has no user-supplied semantic content (OE-002 §3.1: Case's own
    definition is limited to the ownership-boundary role), so there is no
    corresponding CaseValidationError — nothing about Case's own fields
    can ever fail validation. See entity.py.
    """
