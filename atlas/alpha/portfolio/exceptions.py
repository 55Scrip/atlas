"""Domain errors for Atlas Alpha's provisional portfolio module."""
from __future__ import annotations


class AlphaPortfolioError(Exception):
    """Base class for all Alpha portfolio errors."""


class AlphaPortfolioValidationError(AlphaPortfolioError):
    """Raised when investor-supplied portfolio input fails validation."""
