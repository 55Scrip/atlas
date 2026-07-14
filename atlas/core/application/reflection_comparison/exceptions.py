"""Domain errors for Reflection Comparison (ATLAS-011)."""
from __future__ import annotations


class ReflectionComparisonError(Exception):
    """Base class for all Reflection Comparison errors."""


class DuplicateReflectionResponseSelectionError(ReflectionComparisonError):
    """Raised when the same ReflectionResponseId is supplied for both
    halves of a comparison. A comparison requires two different,
    already-preserved Reflection Responses."""


class ReflectionResponseNotOwnedError(ReflectionComparisonError):
    """Raised when a supplied id is not present in the investor's own
    Reflection History — whether because it does not exist at all, or
    because it belongs to a different investor. Deliberately not
    distinguished: Reflection Comparison never reveals which case
    applies."""
