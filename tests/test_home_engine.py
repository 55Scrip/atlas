import json

from typer.testing import CliRunner

from atlas.analysis.portfolio import Portfolio
from atlas.analysis.watchlist import Watchlist
from atlas.cli.main import app
from atlas.home import AtlasHomeEngine, AtlasHomeInput, render_atlas_home
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


def test_home_output_contains_bottom_line_and_rating():
    output = AtlasHomeEngine().build()
    rendered = render_atlas_home(output)

    assert "Bottom Line" in rendered
    assert output.summary.bottom_line
    assert "Atlas Rating:" in rendered
    assert output.summary.atlas_rating


def test_home_caps_priorities_and_monitoring_items():
    output = AtlasHomeEngine().build(
        AtlasHomeInput(
            portfolio=_portfolio(),
            watchlist=_watchlist(),
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert len(output.priorities) <= 3
    assert len(output.monitoring) <= 5


def test_home_avoids_forbidden_recommendation_language():
    rendered = render_atlas_home(
        AtlasHomeEngine().build(
            AtlasHomeInput(
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
        "Urgent",
        "Must Act",
        "Guaranteed",
    )
    for phrase in forbidden:
        assert phrase not in rendered
    assert "Worth monitoring" in rendered or "worth monitoring" in rendered


def test_home_orchestrates_existing_engines():
    output = AtlasHomeEngine().build(
        AtlasHomeInput(
            portfolio=_portfolio(),
            watchlist=_watchlist(),
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert "Portfolio Review Engine" in output.engines_used
    assert "Watchlist Review Engine" in output.engines_used
    assert "Market Health Engine" in output.engines_used
    assert "Atlas Language Engine" in output.engines_used


def test_home_empty_changes_are_handled_gracefully():
    output = AtlasHomeEngine().build()

    assert output.changes_since_last_review == (
        "No meaningful changes supplied since the last review.",
    )
    assert "No meaningful changes supplied" in render_atlas_home(output)


def test_home_quiet_day_communicates_nothing_important_changed():
    output = AtlasHomeEngine().build(
        AtlasHomeInput(
            portfolio=_quiet_portfolio(),
            provider=MockCompanyAnalysisProvider(),
        )
    )
    rendered = render_atlas_home(output)

    assert output.summary.bottom_line == (
        "No meaningful changes since your last review. Your portfolio remains "
        "broadly aligned with your strategy."
    )
    assert output.changes_since_last_review == (
        "No meaningful changes since your last review.",
    )
    assert "No meaningful changes since your last review." in rendered
    assert "Your portfolio remains broadly aligned with your strategy." in rendered


def test_home_quiet_day_uses_one_informational_priority():
    output = AtlasHomeEngine().build(
        AtlasHomeInput(
            portfolio=_quiet_portfolio(),
            provider=MockCompanyAnalysisProvider(),
        )
    )

    assert len(output.priorities) == 1
    assert output.priorities[0].title == "No immediate action appears necessary."
    assert "no meaningful portfolio change" in output.priorities[0].why_it_matters
    assert output.watchlist_highlights == ("No meaningful watchlist developments today.",)
    assert output.decision_journal_reminders == (
        "No decision journal reviews require attention today.",
    )


def test_home_output_remains_concise():
    rendered = render_atlas_home(
        AtlasHomeEngine().build(
            AtlasHomeInput(
                portfolio=_portfolio(),
                watchlist=_watchlist(),
                provider=MockCompanyAnalysisProvider(),
            )
        )
    )

    assert len(rendered.splitlines()) <= 70


def test_home_cli_outputs_primary_briefing(tmp_path):
    portfolio_path = tmp_path / "portfolio.json"
    watchlist_path = tmp_path / "watchlist.json"
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
    watchlist_path.write_text(
        json.dumps({"name": "AI Watchlist", "tickers": ["NVDA", "AMD", "MSFT"]}),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "home",
            "--portfolio",
            str(portfolio_path),
            "--watchlist",
            str(watchlist_path),
        ],
    )

    assert result.exit_code == 0
    assert "Atlas Home" in result.output
    assert "Today's Priorities" in result.output
    assert "What Atlas Is Monitoring" in result.output
