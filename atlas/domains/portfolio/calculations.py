from collections import defaultdict

from atlas.shared import Holding, Portfolio

from atlas.domains.portfolio.models import (
    Allocation,
    Concentration,
    ConcentrationLevel,
    PortfolioSummary,
)


def holding_market_value(holding: Holding) -> float:
    """Return deterministic market value for a holding."""

    if holding.market_value > 0:
        return holding.market_value
    if holding.current_price is not None:
        return max(holding.quantity, 0.0) * max(holding.current_price, 0.0)
    return 0.0


def total_portfolio_value(portfolio: Portfolio) -> float:
    """Return total portfolio value from holding values."""

    return round(sum(holding_market_value(holding) for holding in portfolio.holdings), 6)


def holding_weight(holding: Holding, portfolio: Portfolio) -> float:
    """Return holding weight within the portfolio."""

    total_value = total_portfolio_value(portfolio)
    if total_value <= 0:
        return 0.0
    return round(holding_market_value(holding) / total_value, 6)


def sector_allocation(portfolio: Portfolio) -> tuple[Allocation, ...]:
    """Return deterministic sector allocation."""

    return _allocation_by_attribute(portfolio, "sector", missing_label="Unknown Sector")


def country_allocation(portfolio: Portfolio) -> tuple[Allocation, ...]:
    """Return deterministic country allocation."""

    return _allocation_by_attribute(portfolio, "country", missing_label="Unknown Country")


def top_holdings(portfolio: Portfolio, limit: int = 5) -> tuple[Holding, ...]:
    """Return top holdings by market value, then ticker."""

    ordered = sorted(
        portfolio.holdings,
        key=lambda holding: (-holding_market_value(holding), holding.ticker),
    )
    return tuple(ordered[: max(limit, 0)])


def largest_position(portfolio: Portfolio) -> Holding | None:
    """Return the largest portfolio holding."""

    holdings = top_holdings(portfolio, limit=1)
    return holdings[0] if holdings else None


def cash_weight(portfolio: Portfolio) -> float:
    """Return portfolio weight held in cash-like holdings."""

    total_value = total_portfolio_value(portfolio)
    if total_value <= 0:
        return 0.0
    cash_value = sum(
        holding_market_value(holding)
        for holding in portfolio.holdings
        if _is_cash_holding(holding)
    )
    return round(cash_value / total_value, 6)


def concentration_level(portfolio: Portfolio) -> Concentration:
    """Return a deterministic concentration assessment."""

    total_value = total_portfolio_value(portfolio)
    largest = largest_position(portfolio)
    if total_value <= 0 or largest is None:
        return Concentration(
            level=ConcentrationLevel.LOW,
            largest_holding=None,
            largest_weight=0.0,
            top_five_weight=0.0,
            observations=("Portfolio has no measurable holdings.",),
        )

    largest_weight = holding_weight(largest, portfolio)
    top_five_weight = round(
        sum(holding_market_value(holding) for holding in top_holdings(portfolio, 5)) / total_value,
        6,
    )
    observations: list[str] = []
    if largest_weight >= 0.35:
        level = ConcentrationLevel.HIGH
        observations.append("Largest position is a major share of portfolio value.")
    elif largest_weight >= 0.25:
        level = ConcentrationLevel.ELEVATED
        observations.append("Largest position deserves continued monitoring.")
    elif top_five_weight >= 0.75:
        level = ConcentrationLevel.MODERATE
        observations.append("Top holdings represent most of portfolio value.")
    else:
        level = ConcentrationLevel.LOW
        observations.append("No single position dominates portfolio value.")

    return Concentration(
        level=level,
        largest_holding=largest,
        largest_weight=largest_weight,
        top_five_weight=top_five_weight,
        observations=tuple(observations),
    )


def portfolio_summary(portfolio: Portfolio) -> PortfolioSummary:
    """Return a deterministic portfolio summary."""

    total_value = total_portfolio_value(portfolio)
    cash_value = sum(
        holding_market_value(holding)
        for holding in portfolio.holdings
        if _is_cash_holding(holding)
    )
    concentration = concentration_level(portfolio)
    return PortfolioSummary(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        total_value=total_value,
        number_of_holdings=len(portfolio.holdings),
        largest_holding=concentration.largest_holding,
        largest_weight=concentration.largest_weight,
        cash_value=round(cash_value, 6),
        cash_weight=cash_weight(portfolio),
        sector_allocation=sector_allocation(portfolio),
        country_allocation=country_allocation(portfolio),
        top_holdings=top_holdings(portfolio),
        concentration=concentration,
    )


def _allocation_by_attribute(
    portfolio: Portfolio,
    attribute: str,
    missing_label: str,
) -> tuple[Allocation, ...]:
    total_value = total_portfolio_value(portfolio)
    values: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for holding in portfolio.holdings:
        name = str(getattr(holding, attribute)).strip() or missing_label
        values[name] += holding_market_value(holding)
        counts[name] += 1
    allocations = [
        Allocation(
            name=name,
            market_value=round(value, 6),
            weight=round(value / total_value, 6) if total_value > 0 else 0.0,
            holdings_count=counts[name],
        )
        for name, value in values.items()
    ]
    return tuple(sorted(allocations, key=lambda item: (-item.market_value, item.name)))


def _is_cash_holding(holding: Holding) -> bool:
    return holding.asset_type.lower() == "cash" or holding.ticker.upper() in {"CASH", "USD"}
