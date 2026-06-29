from collections import Counter

from atlas.shared import Portfolio

from atlas.domains.portfolio.calculations import total_portfolio_value
from atlas.domains.portfolio.models import (
    PortfolioIssueSeverity,
    PortfolioValidationIssue,
    PortfolioValidationResult,
)


SUPPORTED_CURRENCIES = {"USD"}


def validate_portfolio(portfolio: Portfolio) -> PortfolioValidationResult:
    """Validate portfolio data and return structured issues."""

    issues: list[PortfolioValidationIssue] = []
    if not portfolio.holdings:
        issues.append(
            PortfolioValidationIssue(
                code="empty_portfolio",
                message="Portfolio has no holdings.",
                severity=PortfolioIssueSeverity.WARNING,
            )
        )

    tickers = [holding.ticker.upper() for holding in portfolio.holdings]
    for ticker, count in sorted(Counter(tickers).items()):
        if ticker and count > 1:
            issues.append(
                PortfolioValidationIssue(
                    code="duplicate_ticker",
                    message=f"{ticker} appears more than once.",
                    severity=PortfolioIssueSeverity.WARNING,
                    ticker=ticker,
                )
            )

    for holding in sorted(portfolio.holdings, key=lambda item: item.ticker):
        ticker = holding.ticker.upper()
        if holding.quantity < 0:
            issues.append(
                PortfolioValidationIssue(
                    code="negative_quantity",
                    message=f"{ticker} has a negative quantity.",
                    severity=PortfolioIssueSeverity.ERROR,
                    ticker=ticker,
                )
            )
        if holding.market_value <= 0 and holding.current_price is None:
            issues.append(
                PortfolioValidationIssue(
                    code="missing_price",
                    message=f"{ticker} has no market value or current price.",
                    severity=PortfolioIssueSeverity.WARNING,
                    ticker=ticker,
                )
            )
        if not holding.sector and holding.asset_type.lower() != "cash":
            issues.append(
                PortfolioValidationIssue(
                    code="missing_sector",
                    message=f"{ticker} is missing sector data.",
                    severity=PortfolioIssueSeverity.INFO,
                    ticker=ticker,
                )
            )
        if not holding.country and holding.asset_type.lower() != "cash":
            issues.append(
                PortfolioValidationIssue(
                    code="missing_country",
                    message=f"{ticker} is missing country data.",
                    severity=PortfolioIssueSeverity.INFO,
                    ticker=ticker,
                )
            )
        if holding.weight < 0 or holding.weight > 1:
            issues.append(
                PortfolioValidationIssue(
                    code="invalid_weight",
                    message=f"{ticker} has an invalid stored weight.",
                    severity=PortfolioIssueSeverity.WARNING,
                    ticker=ticker,
                )
            )
        if holding.currency and holding.currency.upper() not in SUPPORTED_CURRENCIES:
            issues.append(
                PortfolioValidationIssue(
                    code="unsupported_currency",
                    message=f"{ticker} uses {holding.currency}; only USD assumptions are supported.",
                    severity=PortfolioIssueSeverity.WARNING,
                    ticker=ticker,
                )
            )

    if total_portfolio_value(portfolio) <= 0 and portfolio.holdings:
        issues.append(
            PortfolioValidationIssue(
                code="missing_portfolio_value",
                message="Portfolio value cannot be calculated from the available holdings.",
                severity=PortfolioIssueSeverity.ERROR,
            )
        )

    return PortfolioValidationResult(
        is_valid=not any(issue.severity == PortfolioIssueSeverity.ERROR for issue in issues),
        issues=tuple(issues),
    )
