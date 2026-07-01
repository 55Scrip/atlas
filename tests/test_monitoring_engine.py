import json

from typer.testing import CliRunner

from atlas.cli.main import app
from atlas.monitoring import (
    MonitoringEngine,
    MonitoringSignal,
    MonitoringSnapshot,
    render_monitoring_alert,
)
from atlas.providers import MockCompanyAnalysisProvider


def test_monitoring_engine_compares_improved_and_deteriorated_signals():
    previous = MonitoringSnapshot(
        object_type="Company",
        identifier="TEST",
        summary="Previous",
        signals=(
            MonitoringSignal("Quality", 70, "Previous", "Previous quality."),
            MonitoringSignal("Valuation", 80, "Previous", "Previous valuation."),
        ),
        new_risks=(),
        new_opportunities=(),
        monitoring_items=("quality", "valuation"),
        confidence=70,
        importance_score=70,
    )
    current = MonitoringSnapshot(
        object_type="Company",
        identifier="TEST",
        summary="Current",
        signals=(
            MonitoringSignal("Quality", 76, "Current", "Quality improved."),
            MonitoringSignal("Valuation", 72, "Current", "Valuation deteriorated."),
        ),
        new_risks=("Valuation pressure increased.",),
        new_opportunities=("Quality improved.",),
        monitoring_items=("quality", "valuation"),
        confidence=76,
        importance_score=74,
    )

    alert = MonitoringEngine().compare(previous, current)

    assert alert.improved_signals[0].signal_name == "Quality"
    assert alert.deteriorated_signals[0].signal_name == "Valuation"
    assert alert.new_risks == ("Valuation pressure increased.",)
    assert alert.new_opportunities == ("Quality improved.",)


def test_monitoring_engine_monitors_theme_changes():
    alert = MonitoringEngine().monitor_theme("AI infrastructure")
    improved_names = {change.signal_name for change in alert.improved_signals}
    deteriorated_names = {change.signal_name for change in alert.deteriorated_signals}

    assert alert.object_type == "Theme"
    assert alert.identifier == "AI infrastructure"
    assert "Theme confidence" in improved_names
    assert "Electricity supply bottleneck" in deteriorated_names
    assert "HBM supply and pricing" in alert.monitoring_items


def test_monitoring_engine_monitors_market_health_credit():
    alert = MonitoringEngine().monitor_market_health()
    improved_names = {change.signal_name for change in alert.improved_signals}
    deteriorated_names = {change.signal_name for change in alert.deteriorated_signals}

    assert alert.object_type == "Market Health"
    assert "Credit" in improved_names
    assert "Market Breadth" in deteriorated_names
    assert alert.importance_score > 0


def test_monitoring_renderer_includes_required_sections():
    alert = MonitoringEngine().monitor_company("NVDA", MockCompanyAnalysisProvider())

    rendered = render_monitoring_alert(alert)

    assert "Summary" in rendered
    assert "Since last analysis:" in rendered
    assert "Signals that improved" in rendered
    assert "Signals that deteriorated" in rendered
    assert "New risks" in rendered
    assert "New opportunities" in rendered
    assert "Confidence" in rendered
    assert "Importance Score" in rendered
    assert "Atlas recommends monitoring" in rendered


def test_monitoring_cli_monitors_company():
    runner = CliRunner()

    result = runner.invoke(app, ["monitor", "NVDA"])

    assert result.exit_code == 0
    assert "Monitoring Alert" in result.output
    assert "Object: Company - NVDA" in result.output


def test_monitoring_cli_monitors_theme():
    runner = CliRunner()

    result = runner.invoke(app, ["monitor", "theme", "AI infrastructure"])

    assert result.exit_code == 0
    assert "Object: Theme - AI infrastructure" in result.output
    assert "Electricity supply bottleneck" in result.output


def test_monitoring_engine_snapshot_watchlist_from_analysis_matches_snapshot_watchlist():
    # Sprint 92: snapshot_watchlist_from_analysis must produce the same result
    # as snapshot_watchlist when given the same WatchlistAnalysis.
    from atlas.analysis.watchlist import Watchlist, WatchlistEngine

    provider = MockCompanyAnalysisProvider()
    watchlist = Watchlist.from_mapping({"name": "Sprint92", "tickers": ["NVDA", "MSFT"]})
    engine = MonitoringEngine()
    analysis = WatchlistEngine().analyze(watchlist=watchlist, provider=provider)

    via_analysis = engine.snapshot_watchlist_from_analysis(analysis)
    via_watchlist = engine.snapshot_watchlist(watchlist, provider)

    assert via_analysis.object_type == via_watchlist.object_type == "Watchlist"
    assert via_analysis.identifier == via_watchlist.identifier == "Sprint92"
    assert via_analysis.confidence == via_watchlist.confidence == 80
    assert len(via_analysis.signals) == len(via_watchlist.signals) == 3
    assert via_analysis.signals[0].name == via_watchlist.signals[0].name


def test_monitoring_cli_monitors_portfolio(tmp_path):
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
                    },
                    {
                        "ticker": "AAPL",
                        "company": "Apple",
                        "sector": "Consumer Electronics",
                        "country": "United States",
                        "market_cap": 3000000000000,
                        "weight": 0.15,
                        "quality_score": 86,
                        "risk_score": 72,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["monitor", str(portfolio_path)])

    assert result.exit_code == 0
    assert "Object: Portfolio - Portfolio" in result.output
    assert "largest position weight" in result.output
