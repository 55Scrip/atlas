import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio
from atlas.cli.main import app
from atlas.daily import DailyBriefEngine, DailyBriefInput, render_daily_brief
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


def test_daily_brief_builds_required_sections():
    brief = DailyBriefEngine().build()

    section_titles = {section.title for section in brief.sections}

    assert brief.title == "Atlas Daily Brief"
    assert brief.opening_summary
    assert "What Changed" in section_titles
    assert "Portfolio Notes" in section_titles
    assert "Market Notes" in section_titles
    assert "Themes To Watch" in section_titles
    assert "Risks To Watch" in section_titles
    assert "Opportunities To Study" in section_titles
    assert "Has anything important changed?" in brief.suggested_questions


def test_daily_brief_uses_portfolio_context():
    profile = InvestorProfileEngine().create_default_profile(name="Daily User")

    brief = DailyBriefEngine().build(
        DailyBriefInput(
            investor_profile=profile,
            portfolio=_portfolio(),
            provider=MockCompanyAnalysisProvider(),
            target_ticker="AAPL",
        )
    )
    rendered = render_daily_brief(brief)

    assert "Portfolio Notes" in rendered
    assert "Largest Position" in rendered
    assert "Concentration Level" in rendered
    assert "Is my portfolio still aligned with my goals?" in rendered


def test_daily_brief_language_is_calm_and_guardrail_safe():
    rendered = render_daily_brief(DailyBriefEngine().build())

    assert "Strong Buy" not in rendered
    assert "Strong Sell" not in rendered
    assert "Buy" not in rendered
    assert "Sell" not in rendered
    assert "Guaranteed" not in rendered
    assert "Risk-free" not in rendered
    assert "worth monitoring" in rendered.lower()
    assert "not enough information" in rendered.lower()


def test_daily_brief_cli_outputs_clean_text(tmp_path):
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
        ["daily", "brief", "--portfolio", str(portfolio_path), "--ticker", "AAPL"],
    )

    assert result.exit_code == 0
    assert "Atlas Daily Brief" in result.output
    assert "Opening Summary" in result.output
    assert "What Changed" in result.output
    assert "Suggested Questions" in result.output
