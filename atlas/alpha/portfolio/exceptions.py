"""Domain errors for Atlas Alpha's provisional portfolio module."""
from __future__ import annotations


class AlphaPortfolioError(Exception):
    """Base class for all Alpha portfolio errors."""


class AlphaPortfolioValidationError(AlphaPortfolioError):
    """Raised when investor-supplied portfolio input fails validation."""


class AlphaPortfolioNotEstablishedError(AlphaPortfolioError):
    """Raised when an operation requires a portfolio state that does not exist yet."""


class AlphaHoldingNotFoundError(AlphaPortfolioError):
    """Raised when a requested ticker does not match any holding in the current state."""


class OutcomeNotFoundForTradeError(AlphaPortfolioError):
    """Raised when apply-trade references an Outcome id that does not exist in Core."""


class DecisionMismatchError(AlphaPortfolioError):
    """Raised when apply-trade's decisionId does not match the referenced Outcome's own decision."""


class TradeAlreadyAppliedError(AlphaPortfolioError):
    """Raised when apply-trade is called again for an Outcome that already has a trade log entry."""
