import json

from typer.testing import CliRunner

from atlas.analysis.company_analysis import MockCompanyAnalysisProvider
from atlas.analysis.watchlist import (
    Watchlist,
    WatchlistEngine,
    WatchlistRecommendation,
    render_watchlist_analysis,
)
from atlas.cli.main import app


def test_watchlist_from_json_file_loads_name_and_tickers(tmp_path):
    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps({"name": "AI Watchlist", "tickers": ["nvda", "AMD", "MSFT"]}),
        encoding="utf-8",
    )

    watchlist = Watchlist.from_json_file(path)

    assert watchlist.name == "AI Watchlist"
    assert tuple(item.ticker for item in watchlist.items) == ("NVDA", "AMD", "MSFT")


def test_watchlist_engine_ranks_and_identifies_required_signals():
    provider = MockCompanyAnalysisProvider()
    watchlist = Watchlist.from_mapping(
        {"name": "AI Watchlist", "tickers": ["NVDA", "AMD", "MSFT", "AAPL"]}
    )

    analysis = WatchlistEngine().analyze(watchlist=watchlist, provider=provider)

    assert analysis.name == "AI Watchlist"
    assert tuple(item.ticker for item in analysis.ranked_opportunities) == (
        "NVDA",
        "MSFT",
        "AMD",
        "AAPL",
    )
    assert analysis.strongest_opportunity.ticker == "NVDA"
    assert analysis.highest_quality_company.ticker == "NVDA"
    assert analysis.cheapest_valuation.ticker == "AMD"
    assert analysis.highest_risk_company.ticker == "NVDA"
    assert analysis.best_overall == analysis.strongest_opportunity
    assert all(signal.label == "Watch" for signal in analysis.companies_to_watch)
    assert analysis.companies_to_avoid == ()
    assert "Atlas would focus first on NVDA" in analysis.final_atlas_view


def test_watchlist_recommendation_values_are_stable():
    assert WatchlistRecommendation.PRIORITIZE.value == "Prioritize"
    assert WatchlistRecommendation.WATCH.value == "Watch"
    assert WatchlistRecommendation.AVOID.value == "Avoid"


def test_render_watchlist_analysis_includes_required_sections():
    provider = MockCompanyAnalysisProvider()
    watchlist = Watchlist.from_mapping(
        {"name": "AI Watchlist", "tickers": ["NVDA", "AMD", "MSFT", "AAPL"]}
    )
    analysis = WatchlistEngine().analyze(watchlist=watchlist, provider=provider)

    rendered = render_watchlist_analysis(analysis)

    assert "Watchlist name: AI Watchlist" in rendered
    assert "Ranked Opportunities" in rendered
    assert "Best Overall" in rendered
    assert "Best Valuation" in rendered
    assert "Highest Quality" in rendered
    assert "Highest Risk" in rendered
    assert "Final Atlas View" in rendered


def test_watchlist_cli_analyze_is_retired(tmp_path):
    # Sprint 91: atlas watchlist analyze command body retired — no longer a valid command
    path = tmp_path / "watchlist.json"
    path.write_text(
        json.dumps({"name": "AI Watchlist", "tickers": ["NVDA", "AMD", "MSFT", "AAPL"]}),
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["watchlist", "analyze", str(path)])
    assert result.exit_code != 0
