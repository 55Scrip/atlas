"""Domain errors for Atlas Alpha's provisional Watchlist module."""
from __future__ import annotations


class AlphaWatchlistError(Exception):
    """Base class for all Alpha Watchlist errors."""


class AlphaWatchlistValidationError(AlphaWatchlistError):
    """Raised when investor-supplied Watchlist input fails validation."""
