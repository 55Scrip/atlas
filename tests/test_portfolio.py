import json

from typer.testing import CliRunner

from atlas.adapters.portfolio import (
    Portfolio,
    PortfolioPosition,
)
from atlas.cli.main import app


def _sample_portfolio() -> Portfolio:
    return Portfolio(
        positions=(
            PortfolioPosition(
                ticker="AAPL",
                company="Apple",
                sector="Consumer Electronics",
                country="United States",
                market_cap=3_000_000_000_000,
                weight=0.25,
                quality_score=86,
                risk_score=72,
            ),
            PortfolioPosition(
                ticker="MSFT",
                company="Microsoft",
                sector="Software",
                country="United States",
                market_cap=3_400_000_000_000,
                weight=0.20,
                quality_score=90,
                risk_score=78,
            ),
            PortfolioPosition(
                ticker="EVO",
                company="Evolution",
                sector="Gaming Technology",
                country="Sweden",
                market_cap=18_000_000_000,
                weight=0.10,
                quality_score=84,
                risk_score=70,
            ),
        )
    )



def test_portfolio_json_loader_accepts_decimal_and_percent_weights(tmp_path):
    path = tmp_path / "portfolio.json"
    path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "AAPL",
                        "company": "Apple",
                        "sector": "Consumer Electronics",
                        "country": "United States",
                        "market_cap": 3_000_000_000_000,
                        "weight": 25,
                        "quality_score": 86,
                        "risk_score": 72,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    portfolio = Portfolio.from_json_file(path)

    assert portfolio.positions[0].weight == 0.25


def test_portfolio_cli_analyze_is_retired(tmp_path):
    # Sprint 89: atlas portfolio analyze command body retired — no longer a valid command
    path = tmp_path / "portfolio.json"
    path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": position.ticker,
                        "company": position.company,
                        "sector": position.sector,
                        "country": position.country,
                        "market_cap": position.market_cap,
                        "weight": position.weight,
                        "quality_score": position.quality_score,
                        "risk_score": position.risk_score,
                    }
                    for position in _sample_portfolio().positions
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["portfolio", "analyze", str(path), "NVDA"])
    assert result.exit_code != 0
