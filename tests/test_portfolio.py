import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import (
    Portfolio,
    PortfolioIntelligenceEngine,
    PortfolioPosition,
    PortfolioRecommendation,
    get_mock_company_portfolio_profile,
    render_portfolio_analysis,
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


def test_portfolio_engine_analyzes_target_in_portfolio_context():
    portfolio = _sample_portfolio()
    target = get_mock_company_portfolio_profile("NVDA")

    analysis = PortfolioIntelligenceEngine().analyze(portfolio, target)

    assert analysis.ticker == "NVDA"
    assert analysis.recommendation == PortfolioRecommendation.NEUTRAL
    assert analysis.portfolio_score == 69
    assert analysis.diversification_impact.score == 80
    assert analysis.sector_concentration.score == 90
    assert analysis.country_concentration.score == 74
    assert analysis.market_cap_concentration.score == 41
    assert analysis.overlap_with_existing_holdings.score == 92
    assert analysis.expected_portfolio_quality_impact.score == 51
    assert analysis.expected_portfolio_risk_impact.score == 51
    assert "sector concentration" in analysis.final_reasoning.lower()


def test_portfolio_engine_penalizes_existing_holding_overlap():
    portfolio = _sample_portfolio()
    target = get_mock_company_portfolio_profile("AAPL")

    analysis = PortfolioIntelligenceEngine().analyze(portfolio, target)

    assert analysis.overlap_with_existing_holdings.score == 20
    assert analysis.recommendation == PortfolioRecommendation.NEUTRAL


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


def test_render_portfolio_analysis_includes_required_sections():
    analysis = PortfolioIntelligenceEngine().analyze(
        _sample_portfolio(),
        get_mock_company_portfolio_profile("NVDA"),
    )

    rendered = render_portfolio_analysis(analysis)

    assert "Portfolio Recommendation" in rendered
    assert "Diversification Impact" in rendered
    assert "Portfolio Risk Impact" in rendered
    assert "Portfolio Quality Impact" in rendered
    assert "Overlap Analysis" in rendered
    assert "Final Reasoning" in rendered


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
