"""Portfolio domain boundary.

Owns portfolio structure, holdings, allocation context, validation, and
portfolio-level observations.
"""

from atlas.shared import Holding, Portfolio

from atlas.domains.portfolio.calculations import (
    cash_weight,
    concentration_level,
    country_allocation,
    holding_market_value,
    holding_weight,
    largest_position,
    portfolio_summary,
    sector_allocation,
    top_holdings,
    total_portfolio_value,
)
from atlas.domains.portfolio.models import (
    Allocation,
    Concentration,
    ConcentrationLevel,
    PortfolioDomainReview,
    PortfolioIssueSeverity,
    PortfolioObservation,
    PortfolioSnapshot,
    PortfolioSummary,
    PortfolioValidationIssue,
    PortfolioValidationResult,
)
from atlas.domains.portfolio.review import PortfolioReviewEngine
from atlas.domains.portfolio.validation import validate_portfolio

__all__ = [
    "Allocation",
    "Concentration",
    "ConcentrationLevel",
    "Holding",
    "Portfolio",
    "PortfolioDomainReview",
    "PortfolioIssueSeverity",
    "PortfolioObservation",
    "PortfolioReviewEngine",
    "PortfolioSnapshot",
    "PortfolioSummary",
    "PortfolioValidationIssue",
    "PortfolioValidationResult",
    "cash_weight",
    "concentration_level",
    "country_allocation",
    "holding_market_value",
    "holding_weight",
    "largest_position",
    "portfolio_summary",
    "sector_allocation",
    "top_holdings",
    "total_portfolio_value",
    "validate_portfolio",
]
