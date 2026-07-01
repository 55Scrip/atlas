import json

from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.providers import MockCompanyAnalysisProvider, YahooFinanceProviderError


class _FailingProvider:
    def get_company_analysis(self, ticker: str):
        raise YahooFinanceProviderError(f"Yahoo Finance network error for {ticker}: offline")

    def get_portfolio_profile(self, ticker: str):
        raise YahooFinanceProviderError(f"Yahoo Finance network error for {ticker}: offline")


def test_analyze_cli_accepts_yahoo_provider(monkeypatch):
    monkeypatch.setattr("atlas.cli.main.YahooFinanceProvider", MockCompanyAnalysisProvider)
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "NVDA", "--provider", "yahoo"])

    assert result.exit_code == 0
    assert "Investment Report" in result.output
    assert "Company: NVIDIA (NVDA)" in result.output


def test_compare_cli_accepts_yahoo_provider(monkeypatch):
    monkeypatch.setattr("atlas.cli.main.YahooFinanceProvider", MockCompanyAnalysisProvider)
    runner = CliRunner()

    result = runner.invoke(app, ["compare", "NVDA", "AMD", "--provider", "yahoo"])

    assert result.exit_code == 0
    assert "Investment Comparison" in result.output


def test_portfolio_cli_accepts_yahoo_provider(monkeypatch, tmp_path):
    monkeypatch.setattr("atlas.cli.main.YahooFinanceProvider", MockCompanyAnalysisProvider)
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
                        "weight": 0.25,
                        "quality_score": 86,
                        "risk_score": 72,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["portfolio", "analyze", str(path), "NVDA", "--provider", "yahoo"],
    )

    # Sprint 79: atlas portfolio analyze is deprecated — shows deprecation message regardless of provider
    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()
    assert "portfolio summary" in result.output.lower()


def test_watchlist_cli_accepts_yahoo_provider(monkeypatch, tmp_path):
    """Sprint 78: atlas watchlist analyze is deprecated — shows deprecation message regardless of provider."""
    monkeypatch.setattr("atlas.cli.main.YahooFinanceProvider", MockCompanyAnalysisProvider)
    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps({"name": "AI Watchlist", "tickers": ["NVDA", "AMD"]}),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["watchlist", "analyze", str(path), "--provider", "yahoo"])

    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()
    assert "watchlist intelligence" in result.output.lower()


def test_yahoo_provider_errors_are_reported_without_crashing(monkeypatch):
    monkeypatch.setattr("atlas.cli.main.YahooFinanceProvider", _FailingProvider)
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "NVDA", "--provider", "yahoo"])

    assert result.exit_code == 1
    assert "Analysis failed" in result.output
    assert "Yahoo Finance network error for NVDA" in result.output


def test_invalid_provider_name_is_reported_without_crashing():
    runner = CliRunner()

    result = runner.invoke(app, ["analyze", "NVDA", "--provider", "unknown"])

    assert result.exit_code == 1
    assert "Analysis failed" in result.output
    assert "Unknown provider" in result.output
