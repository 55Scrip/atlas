from atlas.shared import Portfolio

from atlas.domains.portfolio.calculations import portfolio_summary
from atlas.domains.portfolio.models import (
    ConcentrationLevel,
    PortfolioDomainReview,
    PortfolioIssueSeverity,
    PortfolioObservation,
    PortfolioSummary,
    PortfolioValidationResult,
)
from atlas.domains.portfolio.validation import validate_portfolio


class PortfolioReviewEngine:
    """Simple deterministic portfolio domain review engine."""

    def review(self, portfolio: Portfolio) -> PortfolioDomainReview:
        summary = portfolio_summary(portfolio)
        validation = validate_portfolio(portfolio)
        observations = _build_observations(summary, validation)
        return PortfolioDomainReview(
            summary=summary,
            validation=validation,
            observations=observations,
        )


def _build_observations(
    summary: PortfolioSummary,
    validation: PortfolioValidationResult,
) -> tuple[PortfolioObservation, ...]:
    observations: list[PortfolioObservation] = [
        PortfolioObservation(
            title="Portfolio Summary",
            detail=(
                f"{summary.portfolio_name} contains {summary.number_of_holdings} holding(s) "
                f"with total value {summary.total_value:.2f}."
            ),
        )
    ]
    if summary.largest_holding is not None:
        observations.append(
            PortfolioObservation(
                title="Largest Holding",
                detail=(
                    f"{summary.largest_holding.ticker} is the largest position at "
                    f"{summary.largest_weight:.1%} of portfolio value."
                ),
                severity=_severity_for_concentration(summary.concentration.level),
            )
        )
    if summary.concentration.level in {
        ConcentrationLevel.ELEVATED,
        ConcentrationLevel.HIGH,
    }:
        observations.append(
            PortfolioObservation(
                title="Concentration",
                detail="Portfolio concentration is worth monitoring.",
                severity=_severity_for_concentration(summary.concentration.level),
            )
        )
    if summary.sector_allocation:
        largest_sector = summary.sector_allocation[0]
        if largest_sector.weight >= 0.4:
            observations.append(
                PortfolioObservation(
                    title="Sector Concentration",
                    detail=(
                        f"{largest_sector.name} represents {largest_sector.weight:.1%} "
                        "of portfolio value."
                    ),
                    severity=PortfolioIssueSeverity.WARNING,
                )
            )
    if summary.country_allocation:
        largest_country = summary.country_allocation[0]
        if largest_country.weight >= 0.6:
            observations.append(
                PortfolioObservation(
                    title="Country Concentration",
                    detail=(
                        f"{largest_country.name} represents {largest_country.weight:.1%} "
                        "of portfolio value."
                    ),
                    severity=PortfolioIssueSeverity.WARNING,
                )
            )
    observations.extend(
        PortfolioObservation(
            title="Data Quality",
            detail=issue.message,
            severity=issue.severity,
        )
        for issue in validation.issues
    )
    return tuple(observations)


def _severity_for_concentration(level: ConcentrationLevel) -> PortfolioIssueSeverity:
    if level == ConcentrationLevel.HIGH:
        return PortfolioIssueSeverity.WARNING
    if level == ConcentrationLevel.ELEVATED:
        return PortfolioIssueSeverity.INFO
    return PortfolioIssueSeverity.INFO
