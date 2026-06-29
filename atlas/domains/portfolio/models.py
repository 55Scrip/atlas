from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from atlas.shared import Holding, Portfolio
from atlas.shared.entities import EntityValue


@dataclass(frozen=True)
class Allocation:
    """Portfolio allocation for a single category such as sector or country."""

    name: str
    market_value: float
    weight: float
    holdings_count: int


class ConcentrationLevel(str, Enum):
    """Deterministic concentration levels for portfolio structure."""

    LOW = "Low"
    MODERATE = "Moderate"
    ELEVATED = "Elevated"
    HIGH = "High"


@dataclass(frozen=True)
class Concentration:
    """Portfolio concentration assessment."""

    level: ConcentrationLevel
    largest_holding: Holding | None
    largest_weight: float
    top_five_weight: float
    observations: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Point-in-time portfolio domain snapshot."""

    portfolio: Portfolio
    timestamp: str
    total_value: float
    source_version: str = "portfolio-domain-v1"
    metadata: Mapping[str, EntityValue] | None = None


@dataclass(frozen=True)
class PortfolioSummary:
    """Deterministic summary of portfolio structure."""

    portfolio_id: str
    portfolio_name: str
    total_value: float
    number_of_holdings: int
    largest_holding: Holding | None
    largest_weight: float
    cash_value: float
    cash_weight: float
    sector_allocation: tuple[Allocation, ...]
    country_allocation: tuple[Allocation, ...]
    top_holdings: tuple[Holding, ...]
    concentration: Concentration


class PortfolioIssueSeverity(str, Enum):
    """Validation severity for portfolio data issues."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


@dataclass(frozen=True)
class PortfolioValidationIssue:
    """Structured portfolio validation issue."""

    code: str
    message: str
    severity: PortfolioIssueSeverity
    ticker: str | None = None


@dataclass(frozen=True)
class PortfolioValidationResult:
    """Validation result that reports issues without crashing callers."""

    is_valid: bool
    issues: tuple[PortfolioValidationIssue, ...]


@dataclass(frozen=True)
class PortfolioObservation:
    """Calm structured portfolio observation."""

    title: str
    detail: str
    severity: PortfolioIssueSeverity = PortfolioIssueSeverity.INFO


@dataclass(frozen=True)
class PortfolioDomainReview:
    """Structured non-advisory portfolio domain review."""

    summary: PortfolioSummary
    validation: PortfolioValidationResult
    observations: tuple[PortfolioObservation, ...]
