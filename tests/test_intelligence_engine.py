import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio, PortfolioPosition
from atlas.cli.main import app
from atlas.intelligence import (
    IntelligenceContext,
    IntelligenceEngine,
    IntelligenceInput,
    render_intelligence_report,
)
from atlas.providers import MockCompanyAnalysisProvider


def test_intelligence_engine_combines_core_atlas_outputs():
    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert report.ticker == "NVDA"
    assert report.investment_report.company == "NVIDIA (NVDA)"
    assert report.theme_analysis.theme.value == "AI infrastructure"
    assert report.market_regime_analysis.regime.value == "Neutral"
    assert report.market_health_report.overall_market_health == "Fragile"
    assert report.decision_result.ticker == "NVDA"
    assert report.confidence > 0


def test_intelligence_report_includes_required_sections_without_trade_labels():
    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
        )
    )

    rendered = render_intelligence_report(report)

    assert "Executive Summary" in rendered
    assert "Structural Tailwinds" in rendered
    assert "Current Market Environment" in rendered
    assert "Company Positioning" in rendered
    assert "Portfolio Impact" in rendered
    assert "Risk Assessment" in rendered
    assert "Atlas Conclusion" in rendered
    assert "What Atlas Is Monitoring" in rendered
    assert "What Could Change Atlas' View" in rendered
    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered


def test_intelligence_engine_uses_portfolio_context_when_supplied():
    portfolio = Portfolio(
        positions=(
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
        )
    )

    report = IntelligenceEngine().analyze(
        IntelligenceInput(
            ticker="NVDA",
            provider=MockCompanyAnalysisProvider(),
            context=IntelligenceContext(portfolio=portfolio),
        )
    )

    assert report.portfolio_analysis is not None
    assert any("Diversification:" in item for item in report.portfolio_impact)
    assert any("Overlap:" in item for item in report.portfolio_impact)


def test_intelligence_cli_outputs_ticker_report():
    runner = CliRunner()

    result = runner.invoke(app, ["intelligence", "analyze", "NVDA"])

    assert result.exit_code == 0
    assert "Atlas Intelligence Report" in result.output
    assert "Ticker: NVDA" in result.output
    assert "Executive Summary" in result.output


def test_intelligence_cli_accepts_portfolio_and_ticker(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3400000000000,
                        "weight": 0.2,
                        "quality_score": 90,
                        "risk_score": 78,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["intelligence", "analyze", str(portfolio_path), "NVDA"])

    assert result.exit_code == 0
    assert "Portfolio Impact" in result.output
    assert "Portfolio fit remains uncertain" not in result.output
