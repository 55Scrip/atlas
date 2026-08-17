"""Domain errors for Atlas Alpha's provisional Watchlist module."""
from __future__ import annotations


class AlphaWatchlistError(Exception):
    """Base class for all Alpha Watchlist errors."""


class AlphaWatchlistValidationError(AlphaWatchlistError):
    """Raised when investor-supplied Watchlist input fails validation."""


class AlphaWatchlistEntryNotFoundError(AlphaWatchlistError):
    """Raised when removing a ticker not currently on the Watchlist.

    Matches the codebase's established delete-of-missing convention
    (Evidence/Judgment/ReasoningTrace/KnowledgeReference/Case/Outcome/
    DecisionContext/Hypothesis all raise a NotFoundError rather than
    being silently idempotent) rather than mirroring `add_ticker`'s own
    idempotence, which governs a different operation (create, not
    delete).
    """
