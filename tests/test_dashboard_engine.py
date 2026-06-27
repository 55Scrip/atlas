import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio
from atlas.cli.main import app
from atlas.dashboard import DashboardEngine, DashboardInput, render_dashboard
from atlas.profile import InvestorProfileEngine
from atlas.providers import MockCompanyAnalysisProvider


def _portfolio() -> Portfolio:
    return Portfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "NVDA",
                    "company": "NVIDIA",
                    "sector": "Semiconductors",
                    "country": "United States",
                    "market_cap": 3_300_000_000_000,
                    "weight": 0.42,
                    "quality_score": 92,
                    "risk_score": 77,
                },
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "United States",
                    "market_cap": 3_400_000_000_000,
                    "weight": 0.28,
                    "quality_score": 90,
                    "risk_score": 78,
                },
            ]
        }
    )


def test_dashboard_builds_required_sections_without_portfolio():
    summary = DashboardEngine().build()

    section_titles = {section.title for section in summary.sections}

    assert summary.title == "Atlas Home Dashboard"
    assert "Good day" in summary.greeting
    assert "Welcome" in section_titles
    assert "Portfolio Overview" in section_titles
    assert "Market Overview" in section_titles
    assert "Themes To Watch" in section_titles
    assert len(summary.todays_observations) >= 3
    assert len(summary.monitoring_items) >= 5
    assert "Has anything important changed?" in summary.suggested_questions


def test_dashboard_uses_portfolio_context_for_overview():
    profile = InvestorProfileEngine().create_default_profile(name="Atlas User")

    summary = DashboardEngine().build(
        DashboardInput(
            investor_profile=profile,
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
            target_ticker="AAPL",
        )
    )

    rendered = render_dashboard(summary)

    assert "Atlas User" in rendered
    assert "Largest Position: NVDA at 42.0%" in rendered
    assert "Concentration Level: High" in rendered
    assert "Target Portfolio Fit" in rendered
    assert "Is my portfolio still aligned with my goals?" in rendered


def test_dashboard_language_avoids_recommendation_guardrails():
    rendered = render_dashboard(DashboardEngine().build())

    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered
    assert "Worth monitoring" in rendered
    assert "May deserve attention" in rendered or "Appears stable" in rendered


def test_dashboard_cli_show_outputs_text_dashboard(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "NVDA",
                        "company": "NVIDIA",
                        "sector": "Semiconductors",
                        "country": "United States",
                        "market_cap": 3_300_000_000_000,
                        "weight": 0.42,
                        "quality_score": 92,
                        "risk_score": 77,
                    },
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3_400_000_000_000,
                        "weight": 0.28,
                        "quality_score": 90,
                        "risk_score": 78,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["dashboard", "show", "--portfolio", str(portfolio_path), "--ticker", "AAPL"],
    )

    assert result.exit_code == 0
    assert "Atlas Home Dashboard" in result.output
    assert "Portfolio Overview" in result.output
    assert "Market Overview" in result.output
    assert "Themes To Watch" in result.output
    assert "Suggested Questions" in result.output
