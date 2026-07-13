"""Domain errors for the reasoning_link module (ATLAS-001 Core Loop).

PROVISIONAL STATUS: this module is a temporary orchestration mechanism,
not a stable domain concept — see entity.py's module docstring and
docs/CoreLoopATLAS001.md.
"""
from __future__ import annotations


class ReasoningLinkError(Exception):
    """Base class for all reasoning_link errors."""


class ReasoningLinkValidationError(ReasoningLinkError):
    """Raised when a link's required id fields are missing.

    No NotFoundError classes exist here: links aren't looked up as a
    primary use case, only written and joined-through by the four
    composite application services.
    """
