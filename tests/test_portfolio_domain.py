from atlas.domains.portfolio import (
    ConcentrationLevel,
    Holding,
    Portfolio,
    PortfolioIssueSeverity,
    PortfolioReviewEngine,
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
    validate_portfolio,
)


def _portfolio() -> Portfolio:
    return Portfolio(
        id="portfolio-1",
        name="Core Portfolio",
        holdings=(
            Holding(
                company_id="nvda",
                ticker="NVDA",
                quantity=10,
                current_price=100,
                sector="Semiconductors",
                country="United States",
            ),
            Holding(
                company_id="msft",
                ticker="MSFT",
                quantity=5,
                current_price=100,
                sector="Software",
                country="United States",
            ),
            Holding(
                company_id="cash",
                ticker="CASH",
                market_value=500,
                sector="Cash",
                country="United States",
                asset_type="cash",
            ),
        ),
    )


def test_portfolio_value_and_holding_weights_are_deterministic() -> None:
    portfolio = _portfolio()

    assert holding_market_value(portfolio.holdings[0]) == 1000
    assert total_portfolio_value(portfolio) == 2000
    assert holding_weight(portfolio.holdings[0], portfolio) == 0.5
    assert cash_weight(portfolio) == 0.25


def test_sector_and_country_allocation_are_sorted_by_value_then_name() -> None:
    portfolio = _portfolio()

    sectors = sector_allocation(portfolio)
    countries = country_allocation(portfolio)

    assert [allocation.name for allocation in sectors] == [
        "Semiconductors",
        "Cash",
        "Software",
    ]
    assert sectors[0].weight == 0.5
    assert countries[0].name == "United States"
    assert countries[0].weight == 1.0


def test_top_holdings_largest_position_and_concentration() -> None:
    portfolio = _portfolio()

    assert [holding.ticker for holding in top_holdings(portfolio, limit=2)] == ["NVDA", "CASH"]
    assert largest_position(portfolio).ticker == "NVDA"

    concentration = concentration_level(portfolio)

    assert concentration.level == ConcentrationLevel.HIGH
    assert concentration.largest_holding.ticker == "NVDA"
    assert concentration.largest_weight == 0.5
    assert concentration.top_five_weight == 1.0


def test_portfolio_summary_captures_core_facts() -> None:
    summary = portfolio_summary(_portfolio())

    assert summary.portfolio_name == "Core Portfolio"
    assert summary.total_value == 2000
    assert summary.number_of_holdings == 3
    assert summary.cash_value == 500
    assert summary.cash_weight == 0.25
    assert summary.largest_holding.ticker == "NVDA"


def test_validation_reports_structured_issues_without_crashing() -> None:
    portfolio = Portfolio(
        id="portfolio-2",
        name="Needs Better Data",
        holdings=(
            Holding(
                company_id="a",
                ticker="ABC",
                quantity=-1,
                weight=1.2,
                currency="SEK",
            ),
            Holding(company_id="b", ticker="ABC", market_value=100),
        ),
    )

    result = validate_portfolio(portfolio)
    issue_codes = [issue.code for issue in result.issues]

    assert result.is_valid is False
    assert "duplicate_ticker" in issue_codes
    assert "negative_quantity" in issue_codes
    assert "missing_price" in issue_codes
    assert "missing_sector" in issue_codes
    assert "missing_country" in issue_codes
    assert "invalid_weight" in issue_codes
    assert "unsupported_currency" in issue_codes


def test_empty_portfolio_behavior_is_safe() -> None:
    portfolio = Portfolio(id="empty", name="Empty")

    validation = validate_portfolio(portfolio)
    summary = portfolio_summary(portfolio)

    assert validation.is_valid is True
    assert validation.issues[0].code == "empty_portfolio"
    assert summary.total_value == 0
    assert summary.largest_holding is None
    assert summary.concentration.level == ConcentrationLevel.LOW


def test_portfolio_review_engine_output_is_calm_and_non_advisory() -> None:
    review = PortfolioReviewEngine().review(_portfolio())
    text = " ".join(
        [observation.title + " " + observation.detail for observation in review.observations]
    )

    assert review.summary.total_value == 2000
    assert any(observation.title == "Largest Holding" for observation in review.observations)
    assert any(observation.title == "Sector Concentration" for observation in review.observations)
    assert any(
        observation.severity == PortfolioIssueSeverity.WARNING
        for observation in review.observations
    )
    assert "buy" not in text.lower()
    assert "sell" not in text.lower()
    assert "guaranteed" not in text.lower()
    assert "risk-free" not in text.lower()


def test_review_reports_missing_data_warnings() -> None:
    portfolio = Portfolio(
        id="portfolio-3",
        name="Incomplete",
        holdings=(Holding(company_id="unknown", ticker="UNK", market_value=100),),
    )

    review = PortfolioReviewEngine().review(portfolio)
    details = [observation.detail for observation in review.observations]

    assert "UNK is missing sector data." in details
    assert "UNK is missing country data." in details
