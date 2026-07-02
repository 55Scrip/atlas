import ast
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


def test_monitoring_engine_snapshot_watchlist_uses_blueprint_intelligence():
    # Sprint 93: snapshot_watchlist now uses Blueprint-aligned Watchlist Intelligence.
    # No provider needed; output is research-driven, not score-driven.
    from atlas.capabilities.watchlist_intelligence import WatchlistInput

    watchlist = WatchlistInput.from_mapping({"name": "Sprint93", "tickers": ["NVDA", "MSFT"]})
    engine = MonitoringEngine()

    snapshot = engine.snapshot_watchlist(watchlist)

    assert snapshot.object_type == "Watchlist"
    assert snapshot.identifier == "Sprint93"
    assert snapshot.confidence == 70
    assert len(snapshot.signals) == 3
    assert snapshot.signals[0].name == "Items needing attention"
    assert snapshot.signals[1].name == "Evidence gaps"
    assert snapshot.signals[2].name == "Open questions"
    assert "item(s)" in snapshot.summary


def test_monitoring_cli_monitors_watchlist(tmp_path):
    import json as _json

    watchlist_path = tmp_path / "watchlist.json"
    watchlist_path.write_text(
        _json.dumps({"name": "Sprint93 Watchlist", "tickers": ["NVDA", "MSFT"]}),
        encoding="utf-8",
    )
    runner = CliRunner()

    result = runner.invoke(app, ["monitor", "watchlist", str(watchlist_path)])

    assert result.exit_code == 0
    assert "Monitoring Alert" in result.output
    assert "Object: Watchlist" in result.output
    assert "Items needing attention" in result.output


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


# --- Sprint 121: monitoring portfolio dependency migration ---

_MONITORING_SOURCE = (
    __import__("pathlib").Path(__file__).parent.parent
    / "atlas"
    / "monitoring"
    / "engine.py"
).read_text()

_MONITORING_TREE = ast.parse(_MONITORING_SOURCE)


def test_sprint121_no_runtime_legacy_portfolio_import():
    """atlas.analysis.portfolio must not be imported at module runtime."""
    for node in _MONITORING_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                continue  # guarded imports are intentional
        if isinstance(node, ast.ImportFrom):
            assert node.module != "atlas.analysis.portfolio", (
                "atlas.analysis.portfolio must be behind TYPE_CHECKING, not a runtime import"
            )


def test_sprint121_future_annotations_present():
    """from __future__ import annotations must be declared."""
    assert "from __future__ import annotations" in _MONITORING_SOURCE


def test_sprint121_type_checking_guard_present():
    """Portfolio must be imported inside an if TYPE_CHECKING: block."""
    for node in _MONITORING_TREE.body:
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                for child in ast.walk(node):
                    if isinstance(child, ast.ImportFrom):
                        names = [alias.name for alias in child.names]
                        if "Portfolio" in names:
                            return
    raise AssertionError("Portfolio is not imported inside TYPE_CHECKING block")


def test_sprint121_snapshot_portfolio_behavior_preserved(tmp_path):
    """snapshot_portfolio produces expected signals with legacy Portfolio objects."""
    from atlas.analysis.portfolio import Portfolio

    portfolio_path = tmp_path / "p.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3_400_000_000_000,
                        "weight": 0.60,
                        "quality_score": 90,
                        "risk_score": 78,
                    },
                    {
                        "ticker": "AAPL",
                        "company": "Apple",
                        "sector": "Consumer Electronics",
                        "country": "United States",
                        "market_cap": 3_000_000_000_000,
                        "weight": 0.40,
                        "quality_score": 86,
                        "risk_score": 72,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    portfolio = Portfolio.from_json_file(portfolio_path)
    snapshot = MonitoringEngine().snapshot_portfolio(portfolio)

    assert snapshot.object_type == "Portfolio"
    assert snapshot.identifier == "Portfolio"
    assert "2 position(s)" in snapshot.summary
    signal_names = {s.name for s in snapshot.signals}
    assert "Average quality" in signal_names
    assert "Average risk profile" in signal_names
    assert "Largest position concentration" in signal_names
    assert "Sector diversification" in signal_names
    assert snapshot.confidence == 78
    assert snapshot.importance_score > 0


def test_sprint121_monitor_portfolio_alert_shape(tmp_path):
    """monitor_portfolio returns a MonitoringAlert with expected shape."""
    from atlas.analysis.portfolio import Portfolio

    portfolio_path = tmp_path / "p.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "NVDA",
                        "company": "NVIDIA",
                        "sector": "Semiconductors",
                        "country": "United States",
                        "market_cap": 2_000_000_000_000,
                        "weight": 1.0,
                        "quality_score": 92,
                        "risk_score": 65,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    portfolio = Portfolio.from_json_file(portfolio_path)
    alert = MonitoringEngine().monitor_portfolio(portfolio)

    assert alert.object_type == "Portfolio"
    assert alert.confidence > 0
    assert alert.importance_score > 0
    rendered = render_monitoring_alert(alert)
    assert "Monitoring Alert" in rendered
    assert "Research Framing" in rendered


def test_sprint121_no_advisory_language_in_monitoring_output(tmp_path):
    """Monitoring output must not contain recommendation or advisory language."""
    from atlas.analysis.portfolio import Portfolio

    portfolio_path = tmp_path / "p.json"
    portfolio_path.write_text(
        json.dumps(
            {
                "positions": [
                    {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "sector": "Software",
                        "country": "United States",
                        "market_cap": 3_400_000_000_000,
                        "weight": 1.0,
                        "quality_score": 90,
                        "risk_score": 78,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    portfolio = Portfolio.from_json_file(portfolio_path)
    alert = MonitoringEngine().monitor_portfolio(portfolio)
    rendered = render_monitoring_alert(alert)

    forbidden = ["strong buy", "buy now", "sell now", "entry point", "exit point", "price target"]
    for phrase in forbidden:
        assert phrase.lower() not in rendered.lower(), f"Found forbidden phrase: {phrase!r}"


def test_sprint121_legacy_portfolio_module_still_active():
    """atlas.analysis.portfolio must still be importable (not deleted)."""
    import atlas.analysis.portfolio as legacy
    assert hasattr(legacy, "Portfolio")
    assert not hasattr(legacy, "PortfolioAnalysis"), (
        "PortfolioAnalysis was deleted in Sprint 132"
    )


def test_sprint121_capability_engine_still_clean():
    """Portfolio Intelligence capability engine must not import from atlas.analysis.portfolio."""
    cap_path = (
        __import__("pathlib").Path(__file__).parent.parent
        / "atlas"
        / "capabilities"
        / "portfolio_intelligence"
        / "engine.py"
    )
    source = cap_path.read_text()
    assert "atlas.analysis.portfolio" not in source
