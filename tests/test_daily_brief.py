import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio
from atlas.analysis.watchlist import Watchlist
from atlas.cli.main import app
from atlas.daily_brief import DailyBriefEngine, DailyBriefInput, render_daily_brief

LegacyDailyBriefEngine = DailyBriefEngine  # alias retained for test readability
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


def _quiet_portfolio() -> Portfolio:
    return Portfolio.from_mapping(
        {
            "positions": [
                {
                    "ticker": "MSFT",
                    "company": "Microsoft",
                    "sector": "Software",
                    "country": "United States",
                    "market_cap": 3_400_000_000_000,
                    "weight": 0.20,
                    "quality_score": 92,
                    "risk_score": 35,
                },
                {
                    "ticker": "TSM",
                    "company": "Taiwan Semiconductor",
                    "sector": "Semiconductors",
                    "country": "Taiwan",
                    "market_cap": 900_000_000_000,
                    "weight": 0.16,
                    "quality_score": 88,
                    "risk_score": 38,
                },
                {
                    "ticker": "NOVO",
                    "company": "Novo Nordisk",
                    "sector": "Healthcare",
                    "country": "Denmark",
                    "market_cap": 450_000_000_000,
                    "weight": 0.14,
                    "quality_score": 90,
                    "risk_score": 32,
                },
            ]
        }
    )


def _watchlist() -> Watchlist:
    return Watchlist.from_mapping(
        {
            "name": "AI Watchlist",
            "tickers": ["NVDA", "AMD", "MSFT"],
        }
    )


def _section_titles(brief) -> set[str]:
    return {section.title for section in brief.sections}


def _section(brief, title: str):
    for section in brief.sections:
        if section.title == title:
            return section
    raise AssertionError(f"Missing section: {title}")


def test_daily_brief_includes_required_v2_sections():
    brief = DailyBriefEngine().build()
    rendered = render_daily_brief(brief)
    titles = _section_titles(brief)

    assert brief.title == "Atlas Daily Brief"
    assert "Bottom Line" in rendered
    assert brief.bottom_line
    assert "What Changed" in titles
    assert "Why It Matters" in titles
    assert "Portfolio Context" in titles
    assert "Watchlist Context" in titles
    assert "Market Context" in titles
    assert "Today's Priorities" in titles
    assert "What Atlas Is Monitoring" in titles
    assert "What Could Change This View" in titles
    assert "Full Reasoning" in titles


def test_daily_brief_quiet_day_behavior_is_calm():
    brief = DailyBriefEngine().build(
        DailyBriefInput(
            portfolio=_quiet_portfolio(),
            provider=MockCompanyAnalysisProvider(),
        )
    )
    rendered = render_daily_brief(brief)
    priorities = _section(brief, "Today's Priorities").items

    assert "No meaningful changes since your last review." in rendered
    assert brief.bottom_line == (
        "No meaningful changes since your last review. Your portfolio remains "
        "broadly aligned with your strategy."
    )
    assert len(priorities) == 1
    assert priorities[0].title == "No immediate action appears necessary."


def test_daily_brief_caps_priorities_and_monitoring_items():
    brief = DailyBriefEngine().build(
        DailyBriefInput(
            portfolio=_portfolio(),
            watchlist=_watchlist(),
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert len(_section(brief, "Today's Priorities").items) <= 3
    assert len(_section(brief, "What Atlas Is Monitoring").items) <= 5


def test_daily_brief_avoids_forbidden_language():
    rendered = render_daily_brief(
        DailyBriefEngine().build(
            DailyBriefInput(
                portfolio=_portfolio(),
                watchlist=_watchlist(),
                provider=MockCompanyAnalysisProvider(),
            )
        )
    )

    forbidden = (
        "Buy",
        "Sell",
        "Strong Buy",
        "Strong Sell",
        "Hold",
        "Urgent",
        "Must Act",
        "Guaranteed",
        "Risk-free",
        "Can't lose",
        "Sure thing",
    )
    for phrase in forbidden:
        assert phrase not in rendered


def test_daily_brief_output_is_deterministic():
    daily_input = DailyBriefInput(
        portfolio=_portfolio(),
        watchlist=_watchlist(),
        provider=MockCompanyAnalysisProvider(),
    )

    first = render_daily_brief(DailyBriefEngine().build(daily_input))
    second = render_daily_brief(DailyBriefEngine().build(daily_input))

    assert first == second


def test_daily_brief_orchestrates_existing_engines():
    brief = DailyBriefEngine().build()

    assert "Atlas Home Engine" in brief.engines_used
    assert "Portfolio Review Engine" in brief.engines_used
    assert "Watchlist Review Engine" in brief.engines_used
    assert "Evidence Quality Engine" in brief.engines_used
    assert "Investor Profile Engine" in brief.engines_used
    assert LegacyDailyBriefEngine is DailyBriefEngine


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
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["daily", "brief", "--portfolio", str(portfolio_path)])

    assert result.exit_code == 0
    assert "Atlas Daily Brief" in result.output
    assert "Bottom Line" in result.output
    assert "What Changed" in result.output
    assert "Why It Matters" in result.output
