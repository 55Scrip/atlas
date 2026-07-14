"""Domain errors for Reflection Exploration (ATLAS-012)."""
from __future__ import annotations


class ReflectionExplorationError(Exception):
    """Base class for all Reflection Exploration errors."""


class UnreachableReflectionResponseError(ReflectionExplorationError):
    """Raised when a supplied id is not present in the investor's own
    Reflection History — whether because it does not exist at all, or
    because it belongs to a different investor. Deliberately not
    distinguished: Reflection Exploration never reveals which case
    applies. Raised for the entire request; no partial scope is ever
    returned."""
